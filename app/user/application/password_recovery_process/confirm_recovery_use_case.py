"""
Módulo para el caso de uso de confirmación del PIN de recuperación de contraseña.

Este módulo contiene la clase ConfirmRecoveryPinUseCase que maneja la lógica
para confirmar el PIN de recuperación de contraseña enviado al usuario.
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import status
from datetime import timedelta
from app.infrastructure.common.datetime_utils import datetime_utc_time
from app.infrastructure.services.pin_service import hash_pin
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.user.infrastructure.orm_models import PasswordRecovery, User
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException, UserHasBeenBlockedException, UserNotRegisteredException
from app.user.infrastructure.orm_models import UserState as UserStateModel

# Constantes para roles
ADMIN_ROLE_NAME = "Administrador de Finca"
WORKER_ROLE_NAME = "Trabajador Agrícola"

# Constantes para estados
ACTIVE_STATE_NAME = "active"
LOCKED_STATE_NAME = "locked"
PENDING_STATE_NAME = "pending"
INACTIVE_STATE_NAME = "inactive"

class ConfirmRecoveryPinUseCase:
    """
    Caso de uso para confirmar el PIN de recuperación de contraseña.

    Esta clase maneja el proceso de confirmación del PIN de recuperación,
    incluyendo la validación del estado del usuario, la verificación del PIN,
    y el manejo de intentos fallidos.

    Attributes:
        db (Session): Sesión de base de datos para operaciones de persistencia.
        user_repository (UserRepository): Repositorio para operaciones relacionadas con usuarios.
        state_validator (UserStateValidator): Validador del estado del usuario.
    """

    def __init__(self, db: Session):
        """
        Inicializa una nueva instancia de ConfirmRecoveryPinUseCase.

        Args:
            db (Session): Sesión de base de datos para operaciones de persistencia.
        """
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)

    def confirm_recovery(self, email: str, pin: str) -> SuccessResponse:
        """
        Confirma el PIN de recuperación de contraseña.

        Este método valida el estado del usuario, verifica la existencia de una solicitud
        de recuperación de contraseña válida, comprueba el PIN proporcionado y maneja
        los intentos fallidos.

        Args:
            email (str): Correo electrónico del usuario.
            pin (str): PIN de recuperación proporcionado por el usuario.

        Returns:
            SuccessResponse: Respuesta indicando que el PIN se confirmó correctamente.

        Raises:
            UserNotRegisteredException: Si el usuario no está registrado.
            DomainException: Si no hay una solicitud de recuperación válida, el PIN ha expirado,
                             el PIN es incorrecto, o hay otros errores.
            UserHasBeenBlockedException: Si el usuario ha sido bloqueado debido a múltiples intentos fallidos.
        """
        user = self.user_repository.get_user_with_password_recovery(email)
        if not user:
            raise UserNotRegisteredException()
            
        state_validation_result = self.state_validator.validate_user_state(
            user,
            allowed_states=[UserState.ACTIVE],
            disallowed_states=[UserState.INACTIVE, UserState.PENDING, UserState.LOCKED]
        )
        if state_validation_result:
            return state_validation_result

        recovery = self.get_last_password_recovery(user.recuperacion_contrasena)
        if not recovery:
            raise DomainException(
                message="No hay un registro de recuperación de contraseña pendiente.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        if self.is_password_recovery_expired(recovery):
            self.user_repository.delete_password_recovery(recovery)
            raise DomainException(
                message="La recuperación de contraseña ha expirado. Por favor, inicie el proceso de recuperación de contraseña nuevamente.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        pin_hash = hash_pin(pin)
        
        recovery_pin = recovery.pin == pin_hash 
        
        if not recovery_pin:
            recovery.intentos += 1
            self.user_repository.update_password_recovery(recovery)
            
            if recovery.intentos >= 3:
                block_time = 10
                self.user_repository.delete_password_recovery(recovery)
                self.block_user(user, timedelta(minutes=block_time))
                raise UserHasBeenBlockedException(block_time)
                
            raise DomainException(
                message="PIN de recuperación incorrecto.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        recovery.pin_confirmado = True
        self.user_repository.update_password_recovery(recovery)
        
        return SuccessResponse(
                message="PIN de recuperación confirmado correctamente."
            )
        
    def is_password_recovery_expired(self, recovery: PasswordRecovery) -> bool:
        """
        Verifica si la recuperación de contraseña ha expirado.

        Args:
            recovery (PasswordRecovery): Objeto de recuperación de contraseña.

        Returns:
            bool: True si la recuperación ha expirado, False en caso contrario.
        """
        return recovery.expiracion < datetime_utc_time()
    
    def get_last_password_recovery(self, recovery: PasswordRecovery) -> Optional[PasswordRecovery]:
        """
        Obtiene la última recuperación de contraseña del usuario.

        Esta función también elimina todas las recuperaciones anteriores a la última.

        Args:
            recovery (PasswordRecovery): Objeto o lista de objetos de recuperación de contraseña.

        Returns:
            Optional[PasswordRecovery]: La última recuperación de contraseña, o None si no hay ninguna.
        """
        if isinstance(recovery, list) and recovery:
            recovery.sort(key=lambda r: r.created_at)
            latest_recovery = recovery[-1]
            for old_recovery in recovery[:-1]:
                self.user_repository.delete_password_recovery(old_recovery)
            return latest_recovery
        return None
    
    def is_user_blocked(self, user: User) -> bool:
        """
        Verifica si el usuario está bloqueado.

        Args:
            user (User): Objeto de usuario a verificar.

        Returns:
            bool: True si el usuario está bloqueado, False en caso contrario.
        """
        return user.locked_until and datetime_utc_time() < user.locked_until and user.state_id == self.get_locked_user_state().id

    def block_user(self, user: User, lock_duration: timedelta) -> bool:
        """
        Bloquea al usuario por un período de tiempo específico.

        Args:
            user (User): Usuario a bloquear.
            lock_duration (timedelta): Duración del bloqueo.

        Returns:
            bool: True si el usuario fue bloqueado exitosamente, False en caso contrario.

        Raises:
            DomainException: Si no se pudo bloquear al usuario.
        """
        try:
            user.locked_until = datetime_utc_time() + lock_duration
            user.state_id = self.get_locked_user_state().id
            if not self.user_repository.update_user(user):
                raise DomainException(
                    message="No se pudo actualizar el estado del usuario.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            if not self.is_user_blocked(user):
                raise DomainException(
                    message="No se pudo bloquear el usuario.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return True
        except Exception as e:
            raise DomainException(
                message=f"Error al bloquear el usuario: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_locked_user_state(self) -> Optional[UserStateModel]:
        """
        Obtiene el estado de usuario bloqueado.

        Returns:
            Optional[UserStateModel]: El estado de usuario bloqueado, o None si no se encuentra.

        Raises:
            DomainException: Si no se pudo obtener el estado de usuario bloqueado.
        """
        locked_state = self.user_repository.get_state_by_name(LOCKED_STATE_NAME)
        if not locked_state:
            raise DomainException(
                message="No se pudo obtener el estado de usuario bloqueado.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return locked_state
