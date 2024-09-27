from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import status
from app.user.domain.schemas import SuccessResponse
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException, UserStateException
from app.infrastructure.services.pin_service import hash_pin
from app.user.domain.user_state_validator import UserState, UserStateValidator

class ConfirmationUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(self.user_repository)
        
    def execute(self, email: str, pin: str) -> dict:
        # Obtener el usuario por correo electrónico
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise DomainException(
                message="Usuario no encontrado.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Validar el estado del usuario
        state_validation_result = self.state_validator.validate_user_state(
            user,
            allowed_states=[UserState.PENDING],
            disallowed_states=[UserState.ACTIVE, UserState.LOCKED, UserState.INACTIVE]
        )
        if state_validation_result:
            return state_validation_result
            
        # Hashear el PIN proporcionado
        pin_hash = hash_pin(pin)
        
        # Obtener el registro de confirmación
        confirm_pin = self.user_repository.get_user_confirmation(user.id, pin_hash)
        
        if not confirm_pin:
            # Manejar intentos fallidos de confirmación
            intentos = self.user_repository.increment_confirmation_attempts(user.id)
            if intentos >= 3:
                # Eliminar confirmación de usuario
                self.user_repository.delete_user_confirmations(user.id)
                # Eliminar usuario
                self.user_repository.delete_user(user)
                raise DomainException(
                    message="Demasiados intentos. Por favor, inténtalo de nuevo más tarde.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )
            raise DomainException(
                message="PIN de confirmación inválido o expirado.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar el estado del usuario a activo
        active_state_id = self.user_repository.get_active_user_state_id()
        if not active_state_id:
            raise UserStateException(
                message="No se pudo encontrar el estado de usuario activo.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                user_state="unknown"
            )
            
            
        self.user_repository.update_user_state(user.id, active_state_id)
        
        # Actualizar el rol de usuario no confirmado a usuario
        unconfirmed_user_role = self.user_repository.get_unconfirmed_user_role()
        if not unconfirmed_user_role:
            raise DomainException(
                message="No se pudo encontrar el rol de usuario 'Usuario no confirmado'.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        confirmed_user_role = self.user_repository.get_registered_user_role()
        if not confirmed_user_role:
            raise DomainException(
                message="No se pudo encontrar el rol de usuario 'Usuario'.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        self.user_repository.change_user_role(user.id, unconfirmed_user_role, confirmed_user_role)
        
        # Eliminar el registro de confirmación
        self.user_repository.delete_user_confirmations(user.id)
        return SuccessResponse(
                    message="Usuario confirmado exitosamente."
                )