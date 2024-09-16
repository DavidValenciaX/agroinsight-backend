from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.user.infrastructure.orm_models.password_recovery_orm_model import RecuperacionContrasena
from app.user.infrastructure.orm_models.user_confirmation_orm_model import ConfirmacionUsuario
from app.user.infrastructure.orm_models.user_orm_model import User
from app.core.security.security_utils import hash_password, verify_password
from app.core.services.email_service import send_email
from app.core.services.pin_service import generate_pin
from app.user.infrastructure.repository import UserRepository
from app.user.domain.exceptions import TooManyConfirmationAttempts
from app.user.domain.schemas import UserCreate, UserInDB

class UserCreationUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    # Métodos relacionados con la creación de usuarios
    def create_user(self, user_data: UserCreate) -> User:
        hashed_password = hash_password(user_data.password)
        
        pending_state = self.user_repository.get_pending_user_state()
        if not pending_state:
            raise ValueError("No se pudo encontrar el estado de usuario pendiente")

        new_user = User(
            nombre=user_data.nombre,
            apellido=user_data.apellido,
            email=user_data.email,
            password=hashed_password,
            state_id=pending_state.id
        )
        created_user = self.user_repository.create_user(new_user)
        
        unconfirmed_role = self.user_repository.get_unconfirmed_user_role()
        if unconfirmed_role:
            self.user_repository.assign_role_to_user(created_user.id, unconfirmed_role.id)
        else:
            raise ValueError("No se pudo encontrar el rol de Usuario No Confirmado")
        
        return created_user

    def create_user_with_confirmation(self, user: UserInDB) -> bool:
        try:
            # Eliminar confirmaciones anteriores si existen
            self.user_repository.delete_user_confirmations(user.id)
            
            # Generar PIN y su hash
            pin, pin_hash = generate_pin()
            confirmation = ConfirmacionUsuario(
                usuario_id=user.id,
                pin=pin_hash,
                expiracion=datetime.utcnow() + timedelta(minutes=10)
            )
            
            # Enviar correo de confirmación
            if self.send_confirmation_email(user.email, pin):
                self.user_repository.add_user_confirmation(confirmation)
                return True
            else:
                return False
        except Exception as e:
            # Manejar excepción (puede mejorarse con un sistema de logging)
            print(f"Error al crear la confirmación del usuario: {str(e)}")
            return False

    def send_confirmation_email(self, email: str, pin: str) -> bool:
        """Envía un correo electrónico con el PIN de confirmación."""
        subject = "Confirma tu registro en AgroInSight"
        text_content = f"Tu PIN de confirmación es: {pin}\nEste PIN expirará en 10 minutos."
        html_content = f"""
        <html>
            <body>
                <p><strong>Tu PIN de confirmación es: {pin}</strong></p>
                <p>Este PIN expirará en 10 minutos.</p>
            </body>
        </html>
        """
        return send_email(email, subject, text_content, html_content)

    def confirm_user(self, user_id: int, pin_hash: str) -> bool:
        confirmation = self.user_repository.get_user_confirmation(user_id, pin_hash)
            
        if not confirmation:
            return False
            
        # Actualizar el estado del usuario a 'active'
        active_state = self.user_repository.get_active_user_state()
        if not active_state:
            # Manejar el caso donde el estado 'active' no existe
            return False
        self.user_repository.update_user_state(user_id, active_state.id)
            
        # Cambiar el rol del usuario de "Usuario No Confirmado" a "Usuario"
        self.user_repository.change_user_role(user_id, "Usuario No Confirmado", "Usuario")
            
        # Eliminar la confirmación
        self.user_repository.delete_user_confirmations(user_id)
            
        return True

    def resend_confirmation_pin(self, email: str) -> bool:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            return False
            
        try:
            # Eliminar la confirmación existente
            self.user_repository.delete_user_confirmations(user.id)
                
            # Crear una nueva confirmación
            pin, pin_hash = generate_pin()
            confirmation = ConfirmacionUsuario(
                usuario_id=user.id,
                pin=pin_hash,
                expiracion=datetime.utcnow() + timedelta(minutes=10)
            )
                
            # Intentar enviar el correo electrónico
            if self.send_confirmation_email(email, pin):
                self.user_repository.add_user_confirmation(confirmation)
                return True
            else:
                return False
        except Exception as e:
            # Manejar excepción
            print(f"Error al reenviar el PIN de confirmación: {str(e)}")
            return False

    def handle_failed_confirmation(self, user_id: int):
        """Maneja los intentos fallidos de confirmación."""
        intentos = self.user_repository.increment_confirmation_attempts(user_id)
        if intentos >= 3:
            user = self.user_repository.get_user_by_id(user_id)
            if user:
                self.user_repository.delete_user_confirmations(user_id)
                self.user_repository.delete_user(user)
                raise TooManyConfirmationAttempts()