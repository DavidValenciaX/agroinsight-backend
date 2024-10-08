"""
Este módulo define las rutas de la API para la gestión de usuarios.

Incluye endpoints para la creación, actualización, eliminación y recuperación de usuarios,
así como para el manejo de autenticación y autorización.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.user.application.admin_use_cases.admin_deactivates_user_use_case import AdminDeactivatesUserUseCase
from app.user.application.admin_use_cases.admin_updates_user_use_case import AdminUpdatesUserUseCase
from app.user.application.admin_use_cases.admin_creates_user_use_case import AdminCreatesUserUseCase
from app.user.application.admin_use_cases.admin_list_users_use_case import AdminListUsersUseCase
from app.user.application.admin_use_cases.admin_get_user_by_id_use_case import AdminGetUserByIdUseCase
from app.user.application.update_user_info_use_case import UpdateUserInfoUseCase
from app.user.application.user_register_process.user_register_use_case import UserCreationUseCase
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
from app.user.domain.schemas import UserCreate, ResendPinConfirmRequest, ConfirmationRequest, LoginRequest, Resend2FARequest, TwoFactorAuthRequest, TokenResponse, UserCreateByAdmin, UserResponse, UserUpdate, AdminUserUpdate, PasswordRecoveryRequest, PinConfirmationRequest, PasswordResetRequest, UserInDB
from app.infrastructure.common.common_exceptions import DomainException, UserStateException
from typing import List

# Crear una instancia de HTTPBearer
security_scheme = HTTPBearer()

user_router = APIRouter(prefix="/user", tags=["user"])

@user_router.post("/register", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(getDb),
):
    """
    Registra un nuevo usuario en el sistema.

    Este endpoint recibe los datos de un nuevo usuario, los valida, y si todo es correcto,
    crea una nueva cuenta de usuario en el sistema.

    Parameters:
        user (UserCreate): Datos del usuario a registrar.
        db (Session): Sesión de base de datos.

    Returns:
        SuccessResponse: Un objeto SuccessResponse con un mensaje indicando que el usuario fue registrado exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante el registro, como datos inválidos o un usuario ya existente.
    """
    creation_use_case = UserCreationUseCase(db)
    # Llamamos al caso de uso sin manejar excepciones aquí
    try:
        return creation_use_case.register_user(user)
    except (DomainException, UserStateException) as e:
        # Permite que los manejadores de excepciones globales de FastAPI manejen las excepciones
        raise e
    except Exception as e:
        # Para cualquier otra excepción no esperada, lanza un error HTTP 500 genérico
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno en el registro de usuario: {str(e)}"
        )
        
@user_router.post("/resend-confirm-pin", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def resend_confirmation_pin_endpoint(
    resend_request: ResendPinConfirmRequest,
    db: Session = Depends(getDb)
):
    """
    Reenvía el PIN de confirmación al correo electrónico del usuario.

    Parameters:
        resend_request (ResendPinConfirmRequest): Solicitud de reenvío de PIN.
        db (Session): Sesión de base de datos.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que el PIN fue reenviado exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante el reenvío del PIN.
    """
    resend_confirmation_use_case = ResendConfirmationUseCase(db)
    try:
        return resend_confirmation_use_case.resend_confirmation(resend_request.email)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al reenviar el PIN de confirmación: {str(e)}"
        )
        
@user_router.post("/confirm", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def confirm_user_registration(
    confirmation: ConfirmationRequest,
    db: Session = Depends(getDb)
):
    """
    Confirma el registro de un usuario utilizando un PIN.

    Parameters:
        confirmation (ConfirmationRequest): Datos de confirmación del usuario.
        db (Session): Sesión de base de datos.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que el registro fue confirmado exitosamente.

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
        )
    
@user_router.post("/login", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def login_for_access_token(login_request: LoginRequest, db: Session = Depends(getDb)):
    """
    Inicia sesión y obtiene un token de acceso.

    Parameters:
        login_request (LoginRequest): Datos de inicio de sesión del usuario.
        db (Session): Sesión de base de datos.

    Returns:
        SuccessResponse: Un objeto SuccessResponse con el token de acceso.

    Raises:
        HTTPException: Si ocurre un error durante el inicio de sesión.
    """
    login_use_case = LoginUseCase(db)
    try:
        return login_use_case.login_user(login_request.email, login_request.password)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al procesar el inicio de sesión: {str(e)}"
        )
    
@user_router.post("/resend-2fa-pin", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def resend_2fa_pin_endpoint(
    resend_request: Resend2FARequest,
    db: Session = Depends(getDb)
):
    """
    Reenvía el PIN de autenticación de dos factores al usuario.

    Parameters:
        resend_request (Resend2FARequest): Solicitud de reenvío de PIN de 2FA.
        db (Session): Sesión de base de datos.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que el PIN de 2FA fue reenviado exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante el reenvío del PIN de 2FA.
    """
    resend_2fa_use_case = Resend2faUseCase(db)
    try:
        return resend_2fa_use_case.resend_2fa(resend_request.email)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al reenviar el PIN de doble factor de autenticación: {str(e)}"
        )
        
@user_router.post("/login/verify", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def verify_login(auth_request: TwoFactorAuthRequest, db: Session = Depends(getDb)):
    """
    Verifica el inicio de sesión utilizando autenticación de dos factores.

    Parameters:
        auth_request (TwoFactorAuthRequest): Datos de autenticación de dos factores.
        db (Session): Sesión de base de datos.

    Returns:
        TokenResponse: Un objeto TokenResponse con el token de acceso.

    Raises:
        HTTPException: Si ocurre un error durante la verificación del inicio de sesión.
    """
    verify_use_case = VerifyUseCase(db)
    try:
        # Ejecuta el caso de uso y obtiene los datos del token
        return verify_use_case.verify_2fa(auth_request.email, auth_request.pin)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al verificar el inicio de sesión: {str(e)}"
        )

@user_router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: UserInDB = Depends(get_current_user), db: Session = Depends(getDb)):
    """
    Obtiene la información del usuario actual.

    Parameters:
        current_user (UserInDB): Usuario actual autenticado.
        db (Session): Sesión de base de datos.

    Returns:
        UserResponse: Un objeto UserResponse con la información del usuario actual.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de la información del usuario.
    """
    me_use_case = GetCurrentUserUseCase(db)
    try:
        return me_use_case.get_current_user(current_user)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener la información del usuario: {str(e)}"
        )
    
@user_router.put("/me/update", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def update_user_info(
    user_update: UserUpdate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Actualiza la información del usuario actual.

    Parameters:
        user_update (UserUpdate): Datos de actualización del usuario.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que la información fue actualizada exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante la actualización de la información del usuario.
    """
    update_use_case = UpdateUserInfoUseCase(db)
    try:
        return update_use_case.update_user_info(current_user, user_update)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo actualizar la información del usuario: {str(e)}"
        )
    
@user_router.post("/password-recovery", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def initiate_password_recovery(
    recovery_request: PasswordRecoveryRequest,
    db: Session = Depends(getDb)
):
    """
    Inicia el proceso de recuperación de contraseña para un usuario.

    Parameters:
        recovery_request (PasswordRecoveryRequest): Solicitud de recuperación de contraseña.
        db (Session): Sesión de base de datos.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que el proceso de recuperación fue iniciado exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante el inicio del proceso de recuperación.
    """
    password_recovery_use_case = PasswordRecoveryUseCase(db)
    try:
        return password_recovery_use_case.recovery_password(recovery_request.email)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al iniciar el proceso de recuperación de contraseña: {str(e)}"
        )
        
@user_router.post("/resend-recovery-pin", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def resend_recovery_pin(
    recovery_request: PasswordRecoveryRequest,
    db: Session = Depends(getDb)
):
    """
    Reenvía el PIN de recuperación de contraseña al usuario.

    Parameters:
        recovery_request (PasswordRecoveryRequest): Solicitud de reenvío de PIN de recuperación.
        db (Session): Sesión de base de datos.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que el PIN de recuperación fue reenviado exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante el reenvío del PIN de recuperación.
    """
    password_recovery_use_case = ResendRecoveryUseCase(db)
    try:
        return password_recovery_use_case.resend_recovery(recovery_request.email)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno en el reenvio del PIN de recuperación de contraseña: {str(e)}"
        )
        
@user_router.post("/confirm-recovery-pin", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def confirm_recovery_pin(
    pin_confirmation: PinConfirmationRequest,
    db: Session = Depends(getDb)
):
    """
    Confirma el PIN de recuperación de contraseña.

    Parameters:
        pin_confirmation (PinConfirmationRequest): Datos de confirmación del PIN de recuperación.
        db (Session): Sesión de base de datos.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que el PIN de recuperación fue confirmado exitosamente.

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
        )
        
@user_router.post("/reset-password", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def reset_password(
    reset_request: PasswordResetRequest,
    db: Session = Depends(getDb)
):
    """
    Restablece la contraseña de un usuario.

    Parameters:
        reset_request (PasswordResetRequest): Solicitud de restablecimiento de contraseña.
        db (Session): Sesión de base de datos.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que la contraseña fue restablecida exitosamente.

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
        )
        
@user_router.post("/logout", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def logout(
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(getDb),
    credentials: HTTPAuthorizationCredentials = Security(security_scheme)
):
    """
    Cierra la sesión del usuario actual.

    Parameters:
        current_user (UserInDB): Usuario actual autenticado.
        db (Session): Sesión de base de datos.
        credentials (HTTPAuthorizationCredentials): Credenciales de autorización HTTP.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que la sesión fue cerrada exitosamente.

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
        )