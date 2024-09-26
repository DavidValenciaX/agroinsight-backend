from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.user.application.deactivate_user_use_case import DeactivateUserUseCase
from app.user.application.update_user_info_use_case import UpdateUserInfoUseCase
from app.user.application.admin_update_user_use_case import AdminUpdateUserUseCase
from app.user.application.user_creation_process.user_creation_use_case import UserCreationUseCase
from app.user.application.login_process.login_use_case import LoginUseCase
from app.user.application.user_creation_by_admin_use_case import UserCreationByAdminUseCase
from app.user.application.password_recovery_process.password_recovery_use_case import PasswordRecoveryUseCase
from app.user.application.user_creation_process.resend_confirmation_use_case import ResendConfirmationUseCase
from app.user.application.user_creation_process.confirmation_use_case import ConfirmationUseCase
from app.user.application.login_process.resend_2fa_use_case import Resend2faUseCase
from app.user.application.login_process.verify_use_case import VerifyUseCase
from app.user.application.list_users_use_case import ListUsersUseCase
from app.user.application.password_recovery_process.resend_recovery_use_case import ResendRecoveryUseCase
from app.user.application.password_recovery_process.confirm_recovery_pin_use_case import ConfirmRecoveryPinUseCase
from app.user.application.password_recovery_process.reset_password_use_case import ResetPasswordUseCase
from app.user.application.get_current_user_use_case import GetCurrentUserUseCase
from app.user.application.get_user_by_id_use_case import GetUserByIdUseCase
from app.user.application.logout_use_case import LogoutUseCase
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.user.domain.schemas import *
from app.infrastructure.common.common_exceptions import DomainException
from typing import List

# Crear una instancia de HTTPBearer
security_scheme = HTTPBearer()

router = APIRouter(prefix="/user", tags=["user"])

# endpoints de usuarios

@router.post("/create", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(getDb),
):
    creation_use_case = UserCreationUseCase(db)
    # Llamamos al caso de uso sin manejar excepciones aquí
    try:
        return creation_use_case.execute(user)
    except DomainException as e:
        # Permite que los manejadores de excepciones globales de FastAPI manejen las excepciones
        raise e
    except Exception as e:
        # Para cualquier otra excepción no esperada, lanza un error HTTP 500 genérico
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno en el registro de usuario: {str(e)}"
        )
        
@router.post("/resend-confirm-pin", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def resend_confirmation_pin_endpoint(
    resend_request: ResendPinConfirmRequest,
    db: Session = Depends(getDb)
):
    resend_confirmation_use_case = ResendConfirmationUseCase(db)
    try:
        return resend_confirmation_use_case.execute(resend_request.email)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al reenviar el PIN de confirmación: {str(e)}"
        )
        
@router.post("/confirm", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def confirm_user_registration(
    confirmation: ConfirmationRequest,
    db: Session = Depends(getDb)
):
    confirmation_use_case = ConfirmationUseCase(db)
    try:
        return confirmation_use_case.execute(confirmation.email, confirmation.pin)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al confirmar el registro de usuario: {str(e)}"
        )
    
@router.post("/login", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def login_for_access_token(login_request: LoginRequest, db: Session = Depends(getDb)):
    login_use_case = LoginUseCase(db)
    try:
        return login_use_case.execute(login_request.email, login_request.password)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al procesar el inicio de sesión: {str(e)}"
        )
    
@router.post("/resend-2fa-pin", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def resend_2fa_pin_endpoint(
    resend_request: Resend2FARequest,
    db: Session = Depends(getDb)
):
    resend_2fa_use_case = Resend2faUseCase(db)
    try:
        return resend_2fa_use_case.execute(resend_request.email)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al reenviar el PIN de doble factor de autenticación: {str(e)}"
        )
        
@router.post("/login/verify", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def verify_login(auth_request: TwoFactorAuthRequest, db: Session = Depends(getDb)):
    verify_use_case = VerifyUseCase(db)
    try:
        # Ejecuta el caso de uso y obtiene los datos del token
        return verify_use_case.execute(auth_request.email, auth_request.pin)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al verificar el inicio de sesión: {str(e)}"
        )

@router.post(
    "/admin/create", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED
)
def create_user_by_admin(
    user: UserCreateByAdmin,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    user_creation_by_admin_use_case = UserCreationByAdminUseCase(db)
    try:
        return user_creation_by_admin_use_case.execute(user, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno en el registro de usuario por el administrador: {str(e)}"
        )

@router.get("/list", response_model=List[UserResponse], status_code=status.HTTP_200_OK)
def list_users(db: Session = Depends(getDb), current_user=Depends(get_current_user)):
    list_users_use_case = ListUsersUseCase(db)
    try:
        return list_users_use_case.execute(current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar los usuarios: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: UserInDB = Depends(get_current_user), db: Session = Depends(getDb)):
    me_use_case = GetCurrentUserUseCase(db)
    try:
        return me_use_case.execute(current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener la información del usuario: {str(e)}"
        )
    
@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_user_by_id(user_id: int, db: Session = Depends(getDb), current_user=Depends(get_current_user)):
    get_user_by_id_use_case = GetUserByIdUseCase(db)
    try:
        return get_user_by_id_use_case.execute(user_id, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener el usuario: {str(e)}"
        )
    
@router.put("/me/update", response_model=UserResponse, status_code=status.HTTP_200_OK)
def update_user_info(
    user_update: UserUpdate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    update_use_case = UpdateUserInfoUseCase(db)
    try:
        return update_use_case.execute(current_user, user_update)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo actualizar la información del usuario: {str(e)}"
        )
    
@router.put("/{user_id}/update", response_model=UserResponse, status_code=status.HTTP_200_OK)
def admin_update_user(
    user_id: int,
    user_update: AdminUserUpdate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    update_user_use_case = AdminUpdateUserUseCase(db)
    try:
        return update_user_use_case.execute(user_id, user_update, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo actualizar la información del usuario: {str(e)}"
        )
    
@router.delete("/{user_id}/deactivate", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def deactivate_user(
    user_id: int, 
    db: Session = Depends(getDb), 
    current_user: UserInDB = Depends(get_current_user)
):
    deactivate_use_case = DeactivateUserUseCase(db)
    try:
        return deactivate_use_case.execute(user_id, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo desactivar el usuario: {str(e)}"
        )
    
@router.post("/password-recovery", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def initiate_password_recovery(
    recovery_request: PasswordRecoveryRequest,
    db: Session = Depends(getDb)
):
    password_recovery_use_case = PasswordRecoveryUseCase(db)
    try:
        return password_recovery_use_case.execute(recovery_request.email)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al iniciar el proceso de recuperación de contraseña: {str(e)}"
        )
        
@router.post("/resend-recovery-pin", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def resend_recovery_pin(
    recovery_request: PasswordRecoveryRequest,
    db: Session = Depends(getDb)
):
    password_recovery_use_case = ResendRecoveryUseCase(db)
    try:
        return password_recovery_use_case.execute(recovery_request.email)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno en el reenvio del PIN de recuperación de contraseña: {str(e)}"
        )
        
@router.post("/confirm-recovery-pin", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def confirm_recovery_pin(
    pin_confirmation: PinConfirmationRequest,
    db: Session = Depends(getDb)
):
    password_recovery_use_case = ConfirmRecoveryPinUseCase(db)
    try:
        return password_recovery_use_case.execute(pin_confirmation.email, pin_confirmation.pin)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al confirmar el PIN de recuperación: {str(e)}"
        )
        
@router.post("/reset-password", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def reset_password(
    reset_request: PasswordResetRequest,
    db: Session = Depends(getDb)
):
    password_recovery_use_case = ResetPasswordUseCase(db)
    try:
        return password_recovery_use_case.execute(reset_request.email, reset_request.new_password)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al reestablecer la contraseña: {str(e)}"
        )
        
@router.post("/logout", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def logout(
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(getDb),
    credentials: HTTPAuthorizationCredentials = Security(security_scheme)
):
    token = credentials.credentials
    logout_use_case = LogoutUseCase(db)
    try:
        return logout_use_case.execute(token, current_user.id)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo cerrar la sesión: {str(e)}"
        )