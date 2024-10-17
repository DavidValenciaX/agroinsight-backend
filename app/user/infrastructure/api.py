"""
Este módulo define las rutas de la API para la gestión de usuarios.

Incluye endpoints para la creación, actualización, eliminación y recuperación de usuarios,
así como para el manejo de autenticación y autorización.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Security, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.user.application.update_user_info_use_case import UpdateUserInfoUseCase
from app.user.application.user_register_process.user_register_use_case import UserRegisterUseCase
from app.user.application.login_process.login_use_case import LoginUseCase
from app.user.application.password_recovery_process.password_recovery_use_case import PasswordRecoveryUseCase
from app.user.application.user_register_process.resend_confirmation_use_case import ResendConfirmationUseCase
from app.user.application.user_register_process.confirmation_use_case import ConfirmationUseCase
from app.user.application.login_process.resend_2fa_use_case import Resend2faUseCase
from app.user.application.login_process.verify_2fa_use_case import VerifyUseCase
from app.user.application.password_recovery_process.resend_recovery_use_case import ResendRecoveryUseCase
from app.user.application.password_recovery_process.confirm_recovery_use_case import ConfirmRecoveryPinUseCase
from app.user.application.password_recovery_process.reset_password_use_case import ResetPasswordUseCase
from app.user.application.get_current_user_use_case import GetCurrentUserUseCase
from app.user.application.logout_use_case import LogoutUseCase
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserCreate, ResendPinConfirmRequest, ConfirmationRequest, LoginRequest, Resend2FARequest, TwoFactorAuthRequest, TokenResponse, UserResponse, UserUpdate, PasswordRecoveryRequest, PinConfirmationRequest, PasswordResetRequest, UserInDB
from app.infrastructure.common.common_exceptions import DomainException, UserStateException
from typing import List

# Crear una instancia de HTTPBearer
security_scheme = HTTPBearer()

user_router = APIRouter(prefix="/user", tags=["user"])

@user_router.post("/register", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(getDb),
) -> SuccessResponse:
    """
    Registra un nuevo usuario en el sistema.

    Args:
        user (UserCreate): Datos del usuario a registrar.
        background_tasks (BackgroundTasks): Tareas en segundo plano.
        db (Session): Sesión de base de datos.

    Returns:
        SuccessResponse: Objeto con mensaje de éxito.

    Raises:
        HTTPException: Si ocurre un error durante el registro.
    """
    creation_use_case = UserRegisterUseCase(db)
    # Llamamos al caso de uso sin manejar excepciones aquí
    try:
        return creation_use_case.register_user(user, background_tasks)
    except (DomainException, UserStateException) as e:
        # Permite que los manejadores de excepciones globales de FastAPI manejen las excepciones
        raise e
    except Exception as e:
        # Para cualquier otra excepción no esperada, lanza un error HTTP 500 genérico
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno en el registro de usuario: {str(e)}"
        ) from e
        
@user_router.post("/resend-confirm-pin", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def resend_confirmation_pin_endpoint(
    resend_request: ResendPinConfirmRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(getDb)
) -> SuccessResponse:
    """
    Reenvía el PIN de confirmación al correo electrónico del usuario.

    Args:
        resend_request (ResendPinConfirmRequest): Solicitud de reenvío de PIN.
        background_tasks (BackgroundTasks): Tareas en segundo plano.
        db (Session): Sesión de base de datos.

    Returns:
        SuccessResponse: Objeto indicando que el PIN fue reenviado exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante el reenvío del PIN.
    """
    resend_confirmation_use_case = ResendConfirmationUseCase(db)
    try:
        return resend_confirmation_use_case.resend_confirmation(resend_request.email, background_tasks)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al reenviar el PIN de confirmación: {str(e)}"
        ) from e
        
@user_router.post("/confirm", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def confirm_user_registration(
    confirmation: ConfirmationRequest,
    db: Session = Depends(getDb)
) -> SuccessResponse:
    """
    Confirma el registro de un usuario utilizando un PIN.

    Args:
        confirmation (ConfirmationRequest): Datos de confirmación del usuario.
        db (Session): Sesión de base de datos.

    Returns:
        SuccessResponse: Objeto indicando que el registro fue confirmado exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante la confirmación del registro.
    """
    confirmation_use_case = ConfirmationUseCase(db)
    try:
        return confirmation_use_case.confirm_user(confirmation.email, confirmation.pin)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al confirmar el registro de usuario: {str(e)}"
        ) from e
    
@user_router.post("/login", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def login_for_access_token(login_request: LoginRequest, background_tasks: BackgroundTasks, db: Session = Depends(getDb)) -> SuccessResponse:
    """
    Inicia el proceso de doble factor de autenticación.

    Args:
        login_request (LoginRequest): Datos de inicio de sesión del usuario.
        background_tasks (BackgroundTasks): Tareas en segundo plano.
        db (Session): Sesión de base de datos.

    Returns:
        SuccessResponse: Objeto con el token de acceso.

    Raises:
        HTTPException: Si ocurre un error durante el inicio de sesión.
    """
    login_use_case = LoginUseCase(db)
    try:
        return login_use_case.login_user(login_request.email, login_request.password, background_tasks)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al procesar el inicio de sesión: {str(e)}"
        ) from e
    
@user_router.post("/resend-2fa-pin", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def resend_2fa_pin_endpoint(
    resend_request: Resend2FARequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(getDb)
) -> SuccessResponse:
    """
    Reenvía el PIN de doble factor de autenticación al usuario.

    Args:
        resend_request (Resend2FARequest): Solicitud de reenvío de PIN de 2FA.
        background_tasks (BackgroundTasks): Tareas en segundo plano.
        db (Session): Sesión de base de datos.

    Returns:
        SuccessResponse: Objeto indicando que el PIN de 2FA fue reenviado exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante el reenvío del PIN de 2FA.
    """
    resend_2fa_use_case = Resend2faUseCase(db)
    try:
        return resend_2fa_use_case.resend_2fa(resend_request.email, background_tasks)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al reenviar el PIN de doble factor de autenticación: {str(e)}"
        ) from e
        
@user_router.post("/login/verify", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def verify_login(auth_request: TwoFactorAuthRequest, db: Session = Depends(getDb)) -> TokenResponse:
    """
    Verifica el inicio de sesión utilizando el PIN de doble factor de autenticación.

    Args:
        auth_request (TwoFactorAuthRequest): Datos de autenticación de dos factores.
        db (Session): Sesión de base de datos.

    Returns:
        TokenResponse: Objeto con el token de acceso.

    Raises:
        HTTPException: Si ocurre un error durante la verificación del inicio de sesión.
    """
    verify_use_case = VerifyUseCase(db)
    try:
        return verify_use_case.verify_2fa(auth_request.email, auth_request.pin)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al verificar el inicio de sesión: {str(e)}"
        ) from e

@user_router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: UserInDB = Depends(get_current_user), db: Session = Depends(getDb)) -> UserResponse:
    """
    Obtiene la información del usuario actual.

    Args:
        current_user (UserInDB): Usuario actual autenticado.
        db (Session): Sesión de base de datos.

    Returns:
        UserResponse: Objeto con la información del usuario actual.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de la información del usuario.
    """
    get_current_user_use_case = GetCurrentUserUseCase(db)
    try:
        return get_current_user_use_case.get_current_user(current_user)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener la información del usuario: {str(e)}"
        ) from e
    
@user_router.put("/me/update", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def update_user_info(
    user_update: UserUpdate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> SuccessResponse:
    """
    Actualiza la información del usuario actual.

    Args:
        user_update (UserUpdate): Datos de actualización del usuario.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        SuccessResponse: Objeto indicando que la información fue actualizada exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante la actualización de la información del usuario.
    """
    update_user_info_use_case = UpdateUserInfoUseCase(db)
    try:
        return update_user_info_use_case.update_user_info(current_user, user_update)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo actualizar la información del usuario: {str(e)}"
        ) from e
    
@user_router.post("/password-recovery", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def initiate_password_recovery(
    recovery_request: PasswordRecoveryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(getDb)
) -> SuccessResponse:
    """
    Inicia el proceso de recuperación de contraseña para un usuario.

    Args:
        recovery_request (PasswordRecoveryRequest): Solicitud de recuperación de contraseña.
        background_tasks (BackgroundTasks): Tareas en segundo plano.
        db (Session): Sesión de base de datos.

    Returns:
        SuccessResponse: Objeto indicando que el proceso de recuperación fue iniciado exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante el inicio del proceso de recuperación.
    """
    password_recovery_use_case = PasswordRecoveryUseCase(db)
    try:
        return password_recovery_use_case.recovery_password(recovery_request.email, background_tasks)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al iniciar el proceso de recuperación de contraseña: {str(e)}"
        ) from e
        
@user_router.post("/resend-recovery-pin", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def resend_recovery_pin(
    recovery_request: PasswordRecoveryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(getDb)
) -> SuccessResponse:
    """
    Reenvía el PIN de recuperación de contraseña al usuario.

    Args:
        recovery_request (PasswordRecoveryRequest): Solicitud de reenvío de PIN de recuperación.
        background_tasks (BackgroundTasks): Tareas en segundo plano.
        db (Session): Sesión de base de datos.

    Returns:
        SuccessResponse: Objeto indicando que el PIN de recuperación fue reenviado exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante el reenvío del PIN de recuperación.
    """
    password_recovery_use_case = ResendRecoveryUseCase(db)
    try:
        return password_recovery_use_case.resend_recovery(recovery_request.email, background_tasks)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno en el reenvio del PIN de recuperación de contraseña: {str(e)}"
        ) from e
        
@user_router.post("/confirm-recovery-pin", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def confirm_recovery_pin(
    pin_confirmation: PinConfirmationRequest,
    db: Session = Depends(getDb)
) -> SuccessResponse:
    """
    Confirma el PIN de recuperación de contraseña.

    Args:
        pin_confirmation (PinConfirmationRequest): Datos de confirmación del PIN de recuperación.
        db (Session): Sesión de base de datos.

    Returns:
        SuccessResponse: Objeto indicando que el PIN de recuperación fue confirmado exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante la confirmación del PIN de recuperación.
    """
    password_recovery_use_case = ConfirmRecoveryPinUseCase(db)
    try:
        return password_recovery_use_case.confirm_recovery(pin_confirmation.email, pin_confirmation.pin)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al confirmar el PIN de recuperación: {str(e)}"
        ) from e
        
@user_router.post("/reset-password", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def reset_password(
    reset_request: PasswordResetRequest,
    db: Session = Depends(getDb)
) -> SuccessResponse:
    """
    Restablece la contraseña de un usuario.

    Args:
        reset_request (PasswordResetRequest): Solicitud de restablecimiento de contraseña.
        db (Session): Sesión de base de datos.

    Returns:
        SuccessResponse: Objeto indicando que la contraseña fue restablecida exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante el restablecimiento de la contraseña.
    """
    password_recovery_use_case = ResetPasswordUseCase(db)
    try:
        return password_recovery_use_case.reset_password(reset_request.email, reset_request.new_password)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al reestablecer la contraseña: {str(e)}"
        ) from e
        
@user_router.post("/logout", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def logout(
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(getDb),
    credentials: HTTPAuthorizationCredentials = Security(security_scheme)
) -> SuccessResponse:
    """
    Cierra la sesión del usuario actual.

    Args:
        current_user (UserInDB): Usuario actual autenticado.
        db (Session): Sesión de base de datos.
        credentials (HTTPAuthorizationCredentials): Credenciales de autorización HTTP.

    Returns:
        SuccessResponse: Objeto indicando que la sesión fue cerrada exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante el cierre de sesión.
    """
    token = credentials.credentials
    logout_use_case = LogoutUseCase(db)
    try:
        return logout_use_case.logout(token, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo cerrar la sesión: {str(e)}"
        ) from e
