
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
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)

    def confirm_recovery(self, email: str, pin: str) -> SuccessResponse:
        user = self.user_repository.get_user_with_password_recovery(email)
        if not user:
            raise UserNotRegisteredException()
            
        # Validar el estado del usuario
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
            
        # Verificar si la recuperación está expirada
        if self.is_password_recovery_expired(recovery):
            # Eliminar la recuperación
            self.user_repository.delete_password_recovery(recovery)
            raise DomainException(
                message="La recuperación de contraseña ha expirado. Por favor, inicie el proceso de recuperación de contraseña nuevamente.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Verificar si el PIN proporcionado coincide
        pin_hash = hash_pin(pin)
        
        recovery_pin = recovery.pin == pin_hash 
        
        if not recovery_pin:
            # PIN incorrecto, incrementar los intentos
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
            
        # Marcar el PIN como confirmado
        recovery.pin_confirmado = True
        self.user_repository.update_password_recovery(recovery)
        
        return SuccessResponse(
                message="PIN de recuperación confirmado correctamente."
            )
        
    def is_password_recovery_expired(self, recovery: PasswordRecovery) -> bool:
        """Verifica si la recuperación de contraseña ha expirado."""
        return recovery.expiracion < datetime_utc_time()
    
    def get_last_password_recovery(self, recovery: PasswordRecovery) -> Optional[PasswordRecovery]:
        """Obtiene la última recuperación de contraseña del usuario."""
        if isinstance(recovery, list) and recovery:
            recovery.sort(key=lambda r: r.created_at)
            latest_recovery = recovery[-1]
            for old_recovery in recovery[:-1]:
                self.user_repository.delete_password_recovery(old_recovery)
            return latest_recovery
        return None
    
    def is_user_blocked(self, user: User) -> bool:
        return user.locked_until and datetime_utc_time() < user.locked_until and user.state_id == self.get_locked_user_state().id

    def block_user(self, user: User, lock_duration: timedelta) -> bool:
        try:
            user.locked_until = datetime_utc_time() + lock_duration
            user.state_id = self.get_locked_user_state().id
            if not self.user_repository.update_user(user):
                raise DomainException(
                    message="No se pudo actualizar el estado del usuario.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Verificación adicional
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
        locked_state = self.user_repository.get_state_by_name(LOCKED_STATE_NAME)
        if not locked_state:
            raise DomainException(
                message="No se pudo obtener el estado de usuario bloqueado.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return locked_state
