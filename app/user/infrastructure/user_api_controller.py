from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import hashlib
from app.user.application.user_creation_use_case import UserCreationUseCase
from app.user.application.user_authentication_use_case import AuthUseCase
from app.user.infrastructure.sql_user_repository import UserRepository
from app.infrastructure.db.connection import getDb
from app.user.domain.user_entities import UserCreate, UserCreationResponse, LoginRequest, TokenResponse, ConfirmationRequest
from app.core.services.email_service import create_user_with_confirmation, confirm_user, handle_failed_confirmation
from app.user.infrastructure.confirmacion_usuario_orm_model import ConfirmacionUsuario
from app.user.infrastructure.user_orm_model import User as UserModel
from app.user.application.two_factor_auth_use_case import TwoFactorAuthUseCase
from app.user.domain.user_entities import TwoFactorAuthRequest

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
        if create_user_with_confirmation(db, new_user):
            return UserCreationResponse(message="Usuario creado. Por favor, revisa tu email para confirmar el registro.")
        else:
            # Si falla la creación de la confirmación o el envío del email, eliminamos el usuario
            db.delete(new_user)
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

# app/user/infrastructure/user_api_controller.py

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
    
    if not confirmation_record:
        handle_failed_confirmation(db, user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN inválido o expirado"
        )
    
    if confirm_user(db, user.id, pin_hash):
        return {"message": "Usuario confirmado exitosamente"}
    else:
        handle_failed_confirmation(db, user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al confirmar el usuario"
        )

@router.post("/login")
async def login_for_access_token(login_request: LoginRequest, db: Session = Depends(getDb)):
    user_repository = UserRepository(db)
    auth_use_case = AuthUseCase(user_repository)

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
    auth_use_case = AuthUseCase(user_repository)
    
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