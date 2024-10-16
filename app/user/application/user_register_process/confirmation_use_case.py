from typing import Optional
from sqlalchemy.orm import Session
from fastapi import status
from app.infrastructure.common.datetime_utils import datetime_utc_time
from app.infrastructure.common.response_models import SuccessResponse
from app.user.infrastructure.orm_models import User, UserConfirmation
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException, UserStateException
from app.infrastructure.services.pin_service import hash_pin
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.user.infrastructure.orm_models import UserState as UserStateModel

# Constantes para roles
ADMIN_ROLE_NAME = "Administrador de Finca"
WORKER_ROLE_NAME = "Trabajador Agrícola"

# Constantes para estados
ACTIVE_STATE_NAME = "active"
LOCKED_STATE_NAME = "locked"
PENDING_STATE_NAME = "pending"
INACTIVE_STATE_NAME = "inactive"

class ConfirmationUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)
        
    def confirm_user(self, email: str, pin: str) -> SuccessResponse:
        # Obtener el usuario por correo electrónico
        user = self.user_repository.get_user_with_confirmation(email)
        if not user:
            raise UserNotRegisteredException()
        
        # Validar el estado del usuario
        state_validation_result = self.state_validator.validate_user_state(
            user,
            allowed_states=[UserState.PENDING],
            disallowed_states=[UserState.ACTIVE, UserState.LOCKED, UserState.INACTIVE]
        )
        if state_validation_result:
            return state_validation_result
        
        # Verificar si hay una confirmación pendiente
        confirmation = self.get_last_confirmation(user.confirmacion)
        if not confirmation:
            raise DomainException(
                message="No hay un registro de confirmación para este usuario.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Verificar si la confirmación está expirada
        if self.is_confirmation_expired(confirmation):
            # Eliminar usuario y con el se elimina su confirmación
            self.user_repository.delete_user(user)
            raise DomainException(
                message="La confirmación ha expirado. Por favor, inicie el proceso de registro nuevamente.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        # Hashear el PIN proporcionado
        pin_hash = hash_pin(pin)
        
        # Obtener el registro de confirmación
        confirm_pin = confirmation.pin == pin_hash
        
        if not confirm_pin:
            # Manejar intentos fallidos de confirmación
            intentos = self.increment_confirmation_attempts(confirmation)
            if intentos >= 3:
                # Eliminar usuario y con el se elimina su confirmación
                self.user_repository.delete_user(user)
                raise DomainException(
                    message="Demasiados intentos. Por favor, inicie el proceso de registro nuevamente.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )
            raise DomainException(
                message="PIN de confirmación incorrecto.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
            
        self.activate_user(user)
        
        # Eliminar el registro de confirmación
        self.user_repository.delete_user_confirmation(confirmation)
        
        return SuccessResponse(
                message="Usuario confirmado exitosamente."
            )
        
    def is_confirmation_expired(self, confirmation: UserConfirmation) -> bool:
        """Verifica si la confirmación ha expirado."""
        return confirmation.expiracion < datetime_utc_time()
    
    def increment_confirmation_attempts(self, confirmation: UserConfirmation) -> int:
        """Incrementa los intentos de confirmación."""
        confirmation.intentos += 1
        self.user_repository.update_user_confirmation(confirmation)
        return confirmation.intentos

        
    def activate_user(self, user: User) -> None:
        """Activa el usuario."""
        # Actualizar el estado del usuario a activo
        active_state = self.get_active_user_state()
        if not active_state:
            raise UserStateException(
                message="No se pudo encontrar el estado de usuario activo.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                user_state="unknown"
            )
        user.state_id = active_state.id
        self.user_repository.update_user(user)

    def get_last_confirmation(self, confirmation: UserConfirmation) -> Optional[UserConfirmation]:
        """Obtiene la última confirmación del usuario."""
        if isinstance(confirmation, list) and confirmation:
            # Ordenar las confirmaciones por fecha de creación de forma ascendente
            confirmation.sort(key=lambda c: c.created_at)
            # Tomar el último registro
            latest_confirmation = confirmation[-1]
            # Eliminar todas las confirmaciones anteriores a la última
            for old_confirmation in confirmation[:-1]:
                self.user_repository.delete_user_confirmation(old_confirmation)
            # Actualizar la variable confirmation para solo trabajar con la última
            return latest_confirmation
        # Si no hay confirmaciones, retornar None
        return None
    
    def get_active_user_state(self) -> Optional[UserStateModel]:
        return self.user_repository.get_state_by_name(ACTIVE_STATE_NAME)