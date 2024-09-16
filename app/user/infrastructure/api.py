from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.user.application.user_creation_use_case import UserCreationUseCase
from app.user.application.authentication_use_case import AuthenticationUseCase
from app.user.infrastructure.repository import UserRepository
from app.infrastructure.db.connection import getDb
from app.core.services.pin_service import hash_pin
from app.core.security.jwt_middleware import get_current_user
from app.user.domain.schemas import UserResponse, UserCreate, UserCreationResponse, LoginRequest, TokenResponse, ConfirmationRequest, UserInDB, UserResponse, TwoFactorAuthRequest, ResendPinRequest, Resend2FARequest, PasswordRecoveryRequest, PasswordResetRequest, PinConfirmationRequest
from app.user.application.password_recovery_use_case import PasswordRecoveryUseCase
from app.user.domain.exceptions import TooManyConfirmationAttempts, TooManyRecoveryAttempts
from typing import List

# Crear una instancia de HTTPBearer
security_scheme = HTTPBearer()

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserInDB = Depends(get_current_user), db: Session = Depends(getDb)):
    
    # Obtener el repositorio de usuarios
    user_repository = UserRepository(db)
    
    # Obtener el estado del usuario
    estado = user_repository.get_state_by_id(current_user.state_id)
    estado_nombre = estado.nombre if estado else "Desconocido"
    
    # Obtener el rol del usuario
    user_role = ", ".join([role.nombre for role in current_user.roles]) if current_user.roles else "Sin rol asignado"
    
    return UserResponse(
        id=current_user.id,
        nombre=current_user.nombre,
        apellido=current_user.apellido,
        email=current_user.email,
        estado=estado_nombre,
        rol=user_role
    )

@router.delete("/{user_id}/deactivate", status_code=status.HTTP_200_OK)
async def deactivate_user(
    user_id: int, 
    db: Session = Depends(getDb), 
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Endpoint para desactivar (inactivar) un usuario en lugar de eliminarlo.
    """
    user_repository = UserRepository(db)

    # Verificar si el usuario existe
    user = user_repository.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    
    # Desactivar el usuario
    success = user_repository.deactivate_user(user_id)
    
    if success:
        return {"message": "Usuario desactivado exitosamente."}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo desactivar el usuario. Intenta nuevamente."
        )

# Endpoint para listar todos los usuarios
@router.get("/list", response_model=List[UserResponse], status_code=status.HTTP_200_OK)
async def list_users(db: Session = Depends(getDb), current_user=Depends(get_current_user)):
    """
    Endpoint para listar todos los usuarios.
    """
    user_repository = UserRepository(db)
    users = user_repository.get_all_users()
    
    if not users:
        raise HTTPException(status_code=404, detail="No se encontraron usuarios.")
    
    # Mapeamos los usuarios a UserResponse para devolver la información formateada
    return [UserResponse(
        id=user.id,
        nombre=user.nombre,
        apellido=user.apellido,
        email=user.email,
        estado=user.estado.nombre,  # Nombre del estado
        rol=", ".join([role.nombre for role in user.roles]) if user.roles else "Sin rol asignado"  # Nombre del primer rol o "Sin rol"
    ) for user in users]
    
@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user_by_id(user_id: int, db: Session = Depends(getDb), current_user=Depends(get_current_user)):
    """
    Endpoint para obtener un usuario por su ID.
    """
    user_repository = UserRepository(db)
    user = user_repository.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    
    # Mapeamos el usuario a UserResponse para devolver la información formateada
    return UserResponse(
        id=user.id,
        nombre=user.nombre,
        apellido=user.apellido,
        email=user.email,
        estado=user.estado.nombre,  # Nombre del estado
        rol=", ".join([role.nombre for role in user.roles]) if user.roles else "Sin rol asignado"
    )
    
@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(getDb),
    credentials: HTTPAuthorizationCredentials = Security(security_scheme)
):
    """
    Cierra la sesión del usuario actual invalidando su token.
    """
    token = credentials.credentials
    user_repository = UserRepository(db)
    
    # Ahora pasas el usuario_id del current_user
    success = user_repository.blacklist_token(token, current_user.id)
    
    if success:
        return {"message": "Sesión cerrada exitosamente."}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo cerrar la sesión. Intenta nuevamente."
        )


@router.post(
    "/create", response_model=UserCreationResponse, status_code=status.HTTP_201_CREATED
)
async def create_user(user: UserCreate, db: Session = Depends(getDb)):
    user_repository = UserRepository(db)
    creation_use_case = UserCreationUseCase(db)

    existing_user = user_repository.get_user_by_email(user.email)
    if existing_user:
        # Verificar si el usuario tiene una confirmación pendiente
        pending_confirmation = user_repository.get_user_pending_confirmation(existing_user.id)
        
        if pending_confirmation:
            # Si hay una confirmación pendiente, la eliminamos junto con el usuario
            db_user = user_repository.get_user_by_id(existing_user.id)
            if db_user:
                user_repository.delete_user(db_user)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario con este correo electrónico ya existe.",
            )

    try:
        new_user = creation_use_case.create_user(user)
        if creation_use_case.create_user_with_confirmation(new_user):
            return UserCreationResponse(message="Usuario creado. Por favor, revisa tu email para confirmar el registro.")
        else:
            # Si falla la creación de la confirmación o el envío del email, eliminamos el usuario
            db_user = user_repository.get_user_by_id(new_user.id)
            if db_user:
                user_repository.delete_user(db_user)
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
    user_repository = UserRepository(db)
    creation_use_case = UserCreationUseCase(db)
    # Hashear el PIN ingresado por el usuario
    pin_hash = hash_pin(confirmation.pin)
    
    # Buscar al usuario por email
    user = user_repository.get_user_by_email(confirmation.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    confirmation_record = user_repository.get_user_confirmation(user.id, pin_hash)
    
    if not confirmation_record:
        try:
            creation_use_case.handle_failed_confirmation(user.id)
        except TooManyConfirmationAttempts as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=e.message
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN inválido o expirado"
        )
    
    try:
        if creation_use_case.confirm_user(user.id, pin_hash):
            return {"message": "Usuario confirmado exitosamente"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al confirmar el usuario"
            )
    except TooManyConfirmationAttempts as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message
        )
    except Exception as e:
        creation_use_case.handle_failed_confirmation(user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al confirmar el usuario: {str(e)}"
        )
        
@router.post("/resend-confirm-pin", status_code=status.HTTP_200_OK)
async def resend_confirmation_pin_endpoint(
    resend_request: ResendPinRequest,
    db: Session = Depends(getDb)
):
    try:
        creation_use_case = UserCreationUseCase(db)
        success = creation_use_case.resend_confirmation_pin(resend_request.email)
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
    auth_use_case = AuthenticationUseCase(db)

    try:
        authenticated_user = auth_use_case.authenticate_user(login_request.email, login_request.password)
        if authenticated_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo electrónico o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Iniciar verificación en dos pasos
        if auth_use_case.initiate_two_factor_auth(authenticated_user):
            return {"message": "Verificación en dos pasos iniciada. Por favor, revise su correo electrónico para obtener el código."}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al iniciar la verificación en dos pasos"
            )
    except HTTPException as e:
        raise e  # Re-lanza la excepción para mantener el mensaje detallado
        
@router.post("/login/verify", response_model=TokenResponse)
async def verify_login(auth_request: TwoFactorAuthRequest, db: Session = Depends(getDb)):
    auth_use_case = AuthenticationUseCase(db)
    
    try:
        user = auth_use_case.verify_two_factor_auth(auth_request.email, auth_request.pin)
        access_token = auth_use_case.create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as e:
        raise e  # Re-lanza la excepción para mantener el mensaje detallado
    
@router.post("/resend-2fa-pin", status_code=status.HTTP_200_OK)
async def resend_2fa_pin_endpoint(
    resend_request: Resend2FARequest,
    db: Session = Depends(getDb)
):
    auth_use_case = AuthenticationUseCase(db)
    try:
        success = auth_use_case.resend_2fa_pin(resend_request.email)
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
    try:
        success = password_recovery_use_case.confirm_recovery_pin(pin_confirmation.email, pin_confirmation.pin)
        if success:
            return {"message": "Código de recuperación confirmado correctamente."}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código de recuperación inválido o expirado."
            )
    except TooManyRecoveryAttempts as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al confirmar el código de recuperación: {str(e)}"
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