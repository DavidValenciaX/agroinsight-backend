from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import status
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.exceptions import DomainException
from app.core.services.pin_service import hash_pin

class ConfirmationUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def execute(self, email: str, pin: str) -> dict:
        # Obtener el usuario por correo electrónico
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise DomainException(
                message="Usuario no encontrado.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar si la cuenta del usuario ya está activa
        active_state_id = self.user_repository.get_active_user_state_id()
        if user.state_id == active_state_id:
            raise DomainException(
                message="La cuenta ya está confirmada y activa.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar si el usuario ha sido eliminado
        inactive_state_id = self.user_repository.get_inactive_user_state_id()
        if user.state_id == inactive_state_id:
            raise DomainException(
                message="El usuario fue eliminado del sistema.",
                status_code=status.HTTP_410_GONE
            )
        
        if user.locked_until:
            user.locked_until = user.locked_until.replace(tzinfo=timezone.utc)

        # Verificar si la cuenta del usuario está bloqueada
        locked_state_id = self.user_repository.get_locked_user_state_id()
        if user.state_id == locked_state_id and user.locked_until > datetime.now(timezone.utc):
            time_left = user.locked_until - datetime.now(timezone.utc)
            raise DomainException(
                message=f"Tu cuenta está bloqueada. Intenta nuevamente en {time_left.seconds // 60} minutos.",
                status_code=status.HTTP_403_FORBIDDEN
            )
            
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
            raise DomainException(
                message="No se pudo encontrar el estado de usuario 'active'.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
        
        return {"message":"Usuario confirmado exitosamente"}