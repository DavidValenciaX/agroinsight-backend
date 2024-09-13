from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import hashlib
from app.user.application.user_creation_use_case import UserCreationUseCase
from app.user.application.user_authentication_use_case import AuthUseCase
from app.user.infrastructure.repositories.sql_user_repository import UserRepository
from app.infrastructure.db.connection import getDb
from app.user.application.user_confirmation_use_case import UserConfirmationUseCase
from app.user.infrastructure.orm_models.user_confirmation_orm_model import ConfirmacionUsuario
from app.user.infrastructure.orm_models.user_orm_model import User as UserModel
from app.user.application.two_factor_auth_use_case import TwoFactorAuthUseCase
from app.core.security.jwt_middleware import get_current_user
from app.user.domain.user_entities import UserResponse
from app.user.domain.user_entities import UserCreate, UserCreationResponse, LoginRequest, TokenResponse, ConfirmationRequest, UserInDB, UserResponse
from app.user.domain.user_entities import TwoFactorAuthRequest, ResendPinRequest, Resend2FARequest
from app.user.infrastructure.orm_models.user_state_orm_model import EstadoUsuario
from app.user.application.password_recovery_use_case import PasswordRecoveryUseCase
from app.user.domain.user_entities import PasswordRecoveryRequest, PasswordResetRequest, PinConfirmationRequest

router = APIRouter(prefix="/user", tags=["user"])

@router.post(
    "/create", response_model=UserCreationResponse, status_code=status.HTTP_201_CREATED
)
async def create_user(user: UserCreate, db: Session = Depends(getDb)):
    user_repository = UserRepository(db)
    creation_use_case = UserCreationUseCase(user_repository)

    existing_user = user_repository.get_user_by_email(user.email)
    if existing_user:
        # Verificar si el usuario existente está en estado pendiente
        pending_confirmation = db.query(ConfirmacionUsuario).filter(
            ConfirmacionUsuario.usuario_id == existing_user.id
        ).first()
        
        if pending_confirmation:
            # Si hay una confirmación pendiente, la eliminamos junto con el usuario
            db_user = db.query(UserModel).filter(UserModel.id == existing_user.id).first()
            if db_user:
                db.delete(db_user)
                db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario con este correo electrónico ya existe.",
            )

    try:
        new_user = creation_use_case.create_user(user)
        user_confirmation_use_case = UserConfirmationUseCase(db)
        if user_confirmation_use_case.create_user_with_confirmation(new_user):
            return UserCreationResponse(message="Usuario creado. Por favor, revisa tu email para confirmar el registro.")
        else:
            # Si falla la creación de la confirmación o el envío del email, eliminamos el usuario
            db_user = db.query(UserModel).filter(UserModel.id == new_user.id).first()
            if db_user:
                db.delete(db_user)
                db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear el usuario o enviar el email de confirmación. Por favor, intenta nuevamente."
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/confirm", status_code=status.HTTP_200_OK)
async def confirm_user_registration(
    confirmation: ConfirmationRequest,
    db: Session = Depends(getDb)
):
    # Hashear el PIN ingresado por el usuario
    pin_hash = hashlib.sha256(confirmation.pin.encode()).hexdigest()
    
    # Buscar al usuario por email
    user = db.query(UserModel).filter(UserModel.email == confirmation.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    confirmation_record = db.query(ConfirmacionUsuario).filter(
        ConfirmacionUsuario.usuario_id == user.id,
        ConfirmacionUsuario.pin == pin_hash
    ).first()
    
    user_confirmation_use_case = UserConfirmationUseCase(db)
    
    if not confirmation_record:
        user_confirmation_use_case.handle_failed_confirmation(user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN inválido o expirado"
        )
    
    try:
        if user_confirmation_use_case.confirm_user(user.id, pin_hash):
            return {"message": "Usuario confirmado exitosamente"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al confirmar el usuario"
            )
    except Exception as e:
        user_confirmation_use_case.handle_failed_confirmation(user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al confirmar el usuario: {str(e)}"
        )
        
@router.post("/resend-pin", status_code=status.HTTP_200_OK)
async def resend_confirmation_pin_endpoint(
    resend_request: ResendPinRequest,
    db: Session = Depends(getDb)
):
    try:
        user_confirmation_use_case = UserConfirmationUseCase(db)
        success = user_confirmation_use_case.resend_confirmation_pin(resend_request.email)
        if success:
            return {"message": "PIN de confirmación reenviado con éxito"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo reenviar el PIN. Verifique el correo electrónico o intente más tarde."
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reenviar el PIN: {str(e)}"
        )

@router.post("/login")
async def login_for_access_token(login_request: LoginRequest, db: Session = Depends(getDb)):
    user_repository = UserRepository(db)
    auth_use_case = AuthUseCase(db)

    # Obtener el usuario
    user = user_repository.get_user_by_email(login_request.email)
    if user:
        # Intentar desbloquear si está bloqueado
        auth_use_case.unlock_user(user)

    # Intentar autenticar al usuario
    try:
        authenticated_user = auth_use_case.authenticate_user(login_request.email, login_request.password)
    except HTTPException as e:
        raise e  # Re-lanza la excepción para mantener el mensaje detallado

    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electrónico o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Iniciar verificación en dos pasos
    two_factor_use_case = TwoFactorAuthUseCase(db)
    if two_factor_use_case.initiate_two_factor_auth(authenticated_user):
        return {"message": "Verificación en dos pasos iniciada. Por favor, revise su correo electrónico para obtener el código."}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al iniciar la verificación en dos pasos"
        )
        
@router.post("/login/verify", response_model=TokenResponse)
async def verify_login(auth_request: TwoFactorAuthRequest, db: Session = Depends(getDb)):
    two_factor_use_case = TwoFactorAuthUseCase(db)
    user_repository = UserRepository(db)
    auth_use_case = AuthUseCase(db)
    
    user = user_repository.get_user_by_email(auth_request.email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if two_factor_use_case.verify_two_factor_pin(user.id, auth_request.pin):
        # Generar y devolver el token de acceso
        access_token = auth_use_case.create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        two_factor_use_case.handle_failed_verification(user.id)
        raise HTTPException(status_code=400, detail="Código de verificación inválido o expirado")
    
@router.post("/resend-2fa-pin", status_code=status.HTTP_200_OK)
async def resend_2fa_pin_endpoint(
    resend_request: Resend2FARequest,
    db: Session = Depends(getDb)
):
    two_factor_use_case = TwoFactorAuthUseCase(db)
    try:
        success = two_factor_use_case.resend_2fa_pin(resend_request.email)
        if success:
            return {"message": "PIN de verificación en dos pasos reenviado con éxito"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo reenviar el PIN. Verifique el correo electrónico o intente más tarde."
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reenviar el PIN: {str(e)}"
        )
        
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserInDB = Depends(get_current_user), db: Session = Depends(getDb)):
    
    # Obtener el repositorio de usuarios
    user_repository = UserRepository(db)
    
    # Obtener el estado del usuario
    estado = user_repository.get_state_by_id(current_user.state_id)
    estado_nombre = estado.nombre if estado else "Desconocido"
    
    # Obtener el rol del usuario
    user_role = current_user.roles[0].nombre if current_user.roles else "Sin rol asignado"
    
    return UserResponse(
        id=current_user.id,
        nombre=current_user.nombre,
        apellido=current_user.apellido,
        email=current_user.email,
        estado=estado_nombre,
        rol=user_role
    )
    
@router.post("/password-recovery", status_code=status.HTTP_200_OK)
async def initiate_password_recovery(
    recovery_request: PasswordRecoveryRequest,
    db: Session = Depends(getDb)
):
    password_recovery_use_case = PasswordRecoveryUseCase(db)
    success = password_recovery_use_case.initiate_password_recovery(recovery_request.email)
    if success:
        return {"message": "Se ha enviado un código de recuperación a tu correo electrónico."}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo iniciar el proceso de recuperación de contraseña. Verifica el correo electrónico e intenta nuevamente."
        )
        
@router.post("/resend-recovery-pin", status_code=status.HTTP_200_OK)
async def resend_recovery_pin(
    recovery_request: PasswordRecoveryRequest,
    db: Session = Depends(getDb)
):
    password_recovery_use_case = PasswordRecoveryUseCase(db)
    success = password_recovery_use_case.resend_recovery_pin(recovery_request.email)
    if success:
        return {"message": "Se ha reenviado el código de recuperación a tu correo electrónico."}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo reenviar el código de recuperación. Verifica el correo electrónico e intenta nuevamente."
        )
        
@router.post("/confirm-recovery-pin", status_code=status.HTTP_200_OK)
async def confirm_recovery_pin(
    pin_confirmation: PinConfirmationRequest,
    db: Session = Depends(getDb)
):
    password_recovery_use_case = PasswordRecoveryUseCase(db)
    pin_hash = hashlib.sha256(pin_confirmation.pin.encode()).hexdigest()
    success = password_recovery_use_case.confirm_recovery_pin(pin_confirmation.email, pin_hash)
    if success:
        return {"message": "Código de recuperación confirmado correctamente."}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de recuperación inválido o expirado."
        )
        
@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    reset_request: PasswordResetRequest,
    db: Session = Depends(getDb)
):
    password_recovery_use_case = PasswordRecoveryUseCase(db)
    success = password_recovery_use_case.reset_password(reset_request.email, reset_request.new_password)
    if success:
        return {"message": "Contraseña restablecida correctamente."}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo restablecer la contraseña. Asegúrate de que la nueva contraseña sea diferente de la anterior y que hayas confirmado el código de recuperación."
        )