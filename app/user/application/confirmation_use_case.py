from sqlalchemy.orm import Session
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.exceptions import TooManyConfirmationAttempts

class ConfirmationUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def handle_failed_confirmation(self, user_id: int):
        """Maneja los intentos fallidos de confirmación."""
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
            # Manejar el caso donde el estado 'active' no existe
            return False
        self.user_repository.update_user_state(user_id, active_state_id)
            
        # Cambiar el rol del usuario de "Usuario No Confirmado" a "Usuario"
        self.user_repository.change_user_role(user_id, "Usuario No Confirmado", "Usuario")
            
        # Eliminar la confirmación
        self.user_repository.delete_user_confirmations(user_id)
            
        return True
