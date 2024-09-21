from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.user.application.user_creation_use_case import UserCreationUseCase
from app.user.application.login_use_case import LoginUseCase
from app.user.application.user_creation_by_admin_use_case import UserCreationByAdminUseCase
from app.user.application.password_recovery_use_case import PasswordRecoveryUseCase
from app.user.application.resend_confirmation_use_case import ResendConfirmationUseCase
from app.user.application.confirmation_use_case import ConfirmationUseCase
from app.user.application.resend_2fa_use_case import Resend2faUseCase
from app.user.application.verify_use_case import VerifyUseCase
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.db.connection import getDb
from app.core.security.jwt_middleware import get_current_user
from app.user.domain.schemas import UserCreateByAdmin, UserResponse, UserCreate, UserCreationResponse, LoginRequest, LoginResponse, TokenResponse, ConfirmationRequest, ResendConfirmationResponse, ConfirmUsuarioResponse, UserInDB, UserResponse, TwoFactorAuthRequest, ResendPinConfirmRequest, Resend2FARequest, Resend2FAResponse, PasswordRecoveryRequest, PasswordResetRequest, PinConfirmationRequest, UserUpdate, AdminUserUpdate
from app.user.domain.exceptions import TooManyRecoveryAttempts, DomainException

from typing import List

# Crear una instancia de HTTPBearer
security_scheme = HTTPBearer()

router = APIRouter(prefix="/user", tags=["user"])

# endpoints de usuarios

@router.post("/create", response_model=UserCreationResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Session = Depends(getDb),
):
    creation_use_case = UserCreationUseCase(db)
    # Llamamos al caso de uso sin manejar excepciones aquí
    try:
        message = creation_use_case.execute(user)
        return UserCreationResponse(message=message)
    except DomainException as e:
        # Permite que los manejadores de excepciones globales de FastAPI manejen las excepciones
        raise e
    except Exception:
        # Para cualquier otra excepción no esperada, lanza un error HTTP 500 genérico
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno en el registro de usuario"
        )
        
@router.post("/resend-confirm-pin", response_model=ResendConfirmationResponse, status_code=status.HTTP_200_OK)
async def resend_confirmation_pin_endpoint(
    resend_request: ResendPinConfirmRequest,
    db: Session = Depends(getDb)
):
    resend_confirmation_use_case = ResendConfirmationUseCase(db)
    try:
        message = resend_confirmation_use_case.execute(resend_request.email)
        return ResendConfirmationResponse(message=message)
    except DomainException as e:
        # Permite que los manejadores de excepciones globales de FastAPI manejen las excepciones
        raise e
    except Exception:
        # Para cualquier otra excepción no esperada, lanza un error HTTP 500 genérico
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al reenviar el PIN de confirmación."
        )
        
@router.post("/confirm", response_model=ConfirmUsuarioResponse, status_code=status.HTTP_200_OK)
async def confirm_user_registration(
    confirmation: ConfirmationRequest,
    db: Session = Depends(getDb)
):
    confirmation_use_case = ConfirmationUseCase(db)
    try:
        message = confirmation_use_case.execute(confirmation.email, confirmation.pin)
        return ConfirmUsuarioResponse(message=message)
    except DomainException as e:
        # Las excepciones serán manejadas por los manejadores globales de FastAPI
        raise e
    except Exception:
        # Para cualquier otra excepción no esperada, lanza un error HTTP 500 genérico
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al confirmar el registro de usuario"
        )
    
@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login_for_access_token(login_request: LoginRequest, db: Session = Depends(getDb)):
    login_use_case = LoginUseCase(db)
    try:
        message = login_use_case.execute(login_request.email, login_request.password)
        return LoginResponse(message=message)
    except DomainException as e:
        # Las excepciones personalizadas serán manejadas por los manejadores globales
        raise e
    except Exception:
        # Para cualquier otra excepción no esperada, lanza un error HTTP 500 genérico
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar el inicio de sesión."
        )
    
@router.post("/resend-2fa-pin", response_model=Resend2FAResponse, status_code=status.HTTP_200_OK)
async def resend_2fa_pin_endpoint(
    resend_request: Resend2FARequest,
    db: Session = Depends(getDb)
):
    resend_2fa_use_case = Resend2faUseCase(db)
    try:
        message = resend_2fa_use_case.execute(resend_request.email)
        return Resend2FAResponse(message=message)
    except DomainException as e:
        # Las excepciones personalizadas serán manejadas por los manejadores globales
        raise e
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al reenviar el PIN de doble factor de autenticación"
        )
        
@router.post("/login/verify", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def verify_login(auth_request: TwoFactorAuthRequest, db: Session = Depends(getDb)):
    verify_use_case = VerifyUseCase(db)
    
    try:
        # Ejecuta el caso de uso y obtiene los datos del token
        token_data = verify_use_case.execute(auth_request.email, auth_request.pin)
        return token_data
    except DomainException as e:
        # Las excepciones serán manejadas por los manejadores globales de FastAPI
        raise e
    except Exception:
        # Para cualquier otra excepción no esperada, lanza un error HTTP 500 genérico
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al verificar el inicio de sesión."
        )

@router.post(
    "/admin/create", response_model=UserCreationResponse, status_code=status.HTTP_201_CREATED
)
async def create_user_by_admin(
    user: UserCreateByAdmin,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    user_creation_by_admin_use_case = UserCreationByAdminUseCase(db)
    try:
        message = user_creation_by_admin_use_case.execute(user, current_user)
        return UserCreationResponse(message = message)
    except DomainException as e:
        # Permite que los manejadores de excepciones globales de FastAPI manejen las excepciones
        raise e
    except Exception:
        # Para cualquier otra excepción no esperada, lanza un error HTTP 500 genérico
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno en el registro de usuario por el administrador"
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
    updated_user = user_repository.update_user_info(current_user, user_update.model_dump(exclude_unset=True))
    
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