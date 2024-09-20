from sqlalchemy.orm import Session
from fastapi import status
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.exceptions import TooManyConfirmationAttempts, DomainException
from app.core.services.pin_service import hash_pin

class ConfirmationUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def execute(self, email: str, pin: str) -> str:
        # Hashear el PIN proporcionado
        pin_hash = hash_pin(pin)
        
        # Obtener el usuario por correo electrónico
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise DomainException(
                message="Usuario no encontrado.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar el estado del usuario
        active_state_id = self.user_repository.get_active_user_state_id()
        if user.state_id == active_state_id:
            raise DomainException(message="La cuenta ya está confirmada y activa.", status_code=400)
        
        # Obtener el registro de confirmación
        confirmation_record = self.user_repository.get_user_confirmation(user.id, pin_hash)
        
        if not confirmation_record:
            # Manejar intentos fallidos de confirmación
            self.handle_failed_confirmation(user.id)
            raise DomainException(
                message="PIN inválido o expirado.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Confirmar al usuario
        success = self.confirm_user(user.id, pin_hash)
        if not success:
            raise DomainException(
                message="Error al confirmar el usuario.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return "Usuario confirmado exitosamente"

    def handle_failed_confirmation(self, user_id: int):
        intentos = self.user_repository.increment_confirmation_attempts(user_id)
        if intentos >= 3:
            user = self.user_repository.get_user_by_id(user_id)
            if user:
                self.user_repository.delete_user_confirmations(user_id)
                self.user_repository.delete_user(user)
                raise TooManyConfirmationAttempts()
    
    def confirm_user(self, user_id: int, pin_hash: str) -> bool:
        confirmation = self.user_repository.get_user_confirmation(user_id, pin_hash)
        if not confirmation:
            return False
        
        # Actualizar el estado del usuario a 'active'
        active_state_id = self.user_repository.get_active_user_state_id()
        if not active_state_id:
            raise DomainException(
                message="No se pudo encontrar el estado 'active' para el usuario.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        self.user_repository.update_user_state(user_id, active_state_id)
        
        # Cambiar el rol del usuario de "Usuario No Confirmado" a "Usuario"
        self.user_repository.change_user_role(user_id, "Usuario No Confirmado", "Usuario")
        
        # Eliminar el registro de confirmación
        self.user_repository.delete_user_confirmations(user_id)
        
        return True