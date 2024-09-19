from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.user.application.user_creation_use_case import UserCreationUseCase
from app.user.application.authentication_use_case import AuthenticationUseCase
from app.user.application.user_creation_by_admin_use_case import UserCreationByAdminUseCase
from app.user.application.password_recovery_use_case import PasswordRecoveryUseCase
from app.user.application.resend_confirmation_use_case import ResendConfirmationUseCase
from app.user.application.confirmation_use_case import ConfirmationUseCase
from app.user.application.resend_2fa_use_case import Resend2faUseCase
from app.user.application.verify_use_case import VerifyUseCase
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.db.connection import getDb
from app.core.services.pin_service import hash_pin
from app.core.security.jwt_middleware import get_current_user
from app.user.domain.schemas import UserCreateByAdmin, UserResponse, UserCreate, UserCreationResponse, LoginRequest, TokenResponse, ConfirmationRequest, UserInDB, UserResponse, TwoFactorAuthRequest, ResendPinConfirmRequest, Resend2FARequest, PasswordRecoveryRequest, PasswordResetRequest, PinConfirmationRequest, UserUpdate, AdminUserUpdate
from app.user.domain.exceptions import TooManyConfirmationAttempts, TooManyRecoveryAttempts
from app.core.security.security_utils import create_access_token

from typing import List

# Crear una instancia de HTTPBearer
security_scheme = HTTPBearer()

router = APIRouter(prefix="/user", tags=["user"])

# endpoints de usuarios

@router.post(
    "/create", response_model=UserCreationResponse, status_code=status.HTTP_201_CREATED
)
async def create_user(
    user: UserCreate,
    db: Session = Depends(getDb),
):
    creation_use_case = UserCreationUseCase(db)
    # Llamamos al caso de uso sin manejar excepciones aquí
    message = creation_use_case.execute(user)
    return UserCreationResponse(message=message)
        
@router.post("/resend-confirm-pin", status_code=status.HTTP_200_OK)
async def resend_confirmation_pin_endpoint(
    resend_request: ResendPinConfirmRequest,
    db: Session = Depends(getDb)
):
    try:
        resend_confirmation_use_case = ResendConfirmationUseCase(db)
        success = resend_confirmation_use_case.resend_confirmation_pin(resend_request.email)
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
        
@router.post("/confirm", status_code=status.HTTP_200_OK)
async def confirm_user_registration(
    confirmation: ConfirmationRequest,
    db: Session = Depends(getDb)
):
    user_repository = UserRepository(db)
    confirmation_use_case = ConfirmationUseCase(db)
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
            confirmation_use_case.handle_failed_confirmation(user.id)
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
        if confirmation_use_case.confirm_user(user.id, pin_hash):
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
        confirmation_use_case.handle_failed_confirmation(user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al confirmar el usuario: {str(e)}"
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
        raise e
    
@router.post("/resend-2fa-pin", status_code=status.HTTP_200_OK)
async def resend_2fa_pin_endpoint(
    resend_request: Resend2FARequest,
    db: Session = Depends(getDb)
):
    resend_2fa_use_case = Resend2faUseCase(db)
    try:
        success = resend_2fa_use_case.resend_2fa_pin(resend_request.email)
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
        
@router.post("/login/verify", response_model=TokenResponse)
async def verify_login(auth_request: TwoFactorAuthRequest, db: Session = Depends(getDb)):
    verify_use_case = VerifyUseCase(db)
    
    try:
        user = verify_use_case.verify_two_factor_auth(auth_request.email, auth_request.pin)
        access_token = create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as e:
        raise e

@router.post(
    "/admin/create", response_model=UserCreationResponse, status_code=status.HTTP_201_CREATED
)
async def create_user_by_admin(
    user: UserCreateByAdmin,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    user_creation_by_admin_use_case = UserCreationByAdminUseCase(db)
    response = user_creation_by_admin_use_case.execute(user, current_user)
    return response

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
    
@router.put("/me/update", response_model=UserResponse)
async def update_user_info(
    user_update: UserUpdate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Endpoint para que el usuario actualice su información.
    """
    user_repository = UserRepository(db)
    
    # Verificar si el email ya está en uso por otro usuario
    if user_update.email and user_update.email != current_user.email:
        existing_user = user_repository.get_user_by_email(user_update.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso por otro usuario."
            )
    
    # Actualizar la información del usuario
    updated_user = user_repository.update_user_info(current_user, user_update.dict(exclude_unset=True))
    
    if updated_user:
        return UserResponse(
            id=updated_user.id,
            nombre=updated_user.nombre,
            apellido=updated_user.apellido,
            email=updated_user.email,
            estado=updated_user.estado.nombre,
            rol=", ".join([role.nombre for role in updated_user.roles]) if updated_user.roles else "Sin rol asignado"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo actualizar la información del usuario."
        )
    
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
    
@router.put("/{user_id}/update", response_model=UserResponse)
async def admin_update_user(
    user_id: int,
    user_update: AdminUserUpdate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Endpoint para que un administrador actualice la información de un usuario.
    """
    user_repository = UserRepository(db)

    # Obtener los roles que tienen permisos administrativos
    admin_roles = user_repository.get_admin_roles()

    # Verificar si el usuario actual tiene uno de los roles administrativos
    if not any(role.id in [admin_role.id for admin_role in admin_roles] for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción."
        )

    # Verificar si el usuario a actualizar existe
    user_to_update = user_repository.get_user_by_id(user_id)
    if not user_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )

    # Verificar si el nuevo email está en uso por otro usuario
    if user_update.email and user_update.email != user_to_update.email:
        existing_user = user_repository.get_user_by_email(user_update.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso por otro usuario."
            )

    # Actualizar la información del usuario
    updated_user = user_repository.update_user_info_by_admin(user_to_update, user_update.model_dump(exclude_unset=True))

    if updated_user:
        return UserResponse(
            id=updated_user.id,
            nombre=updated_user.nombre,
            apellido=updated_user.apellido,
            email=updated_user.email,
            estado=updated_user.estado.nombre,
            rol=", ".join([role.nombre for role in updated_user.roles]) if updated_user.roles else "Sin rol asignado"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo actualizar la información del usuario."
        )
    
@router.delete("/{user_id}/deactivate", status_code=status.HTTP_200_OK)
async def deactivate_user(
    user_id: int, 
    db: Session = Depends(getDb), 
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Endpoint para eliminar (inactivar) un usuario en lugar de eliminarlo.
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