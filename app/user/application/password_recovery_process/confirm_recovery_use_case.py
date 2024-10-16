
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
    
    def block_user(self, user: User, lock_duration: timedelta) -> bool:
        user.locked_until = datetime_utc_time() + lock_duration
        user.state_id = self.user_repository.get_locked_user_state_id()
        return self.user_repository.update_user(user)
