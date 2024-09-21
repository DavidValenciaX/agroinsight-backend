from datetime import timedelta, datetime, timezone
from sqlalchemy.orm import Session
from fastapi import status
from app.user.infrastructure.orm_models import VerificacionDospasos
from app.user.domain.schemas import UserInDB
from app.user.infrastructure.sql_repository import UserRepository
from app.core.services.pin_service import generate_pin
from app.core.services.email_service import send_email
from app.core.security.security_utils import verify_password
from app.user.domain.exceptions import DomainException

class LoginUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def execute(self, email: str, password: str) -> str:
        user = self.authenticate_user(email, password)
        if self.initiate_two_factor_auth(user):
            return "Verificación en dos pasos iniciada. Por favor, revise su correo electrónico para obtener el código."
        else:
            raise DomainException(
                message="Error al iniciar la verificación en dos pasos.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def authenticate_user(self, email: str, password: str) -> UserInDB:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise DomainException(
                message="Usuario no encontrado.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        # Intentar desbloquear si está bloqueado y el tiempo de bloqueo ha pasado
        locked_state_id = self.user_repository.get_locked_user_state_id()
        if user.state_id == locked_state_id:
            self.unlock_user(user)
            # Recargar el usuario después del desbloqueo
            user = self.user_repository.get_user_by_email(email)
        
        active_state_id = self.user_repository.get_active_user_state_id()
        if user.state_id != active_state_id:
            raise DomainException(
                message="La cuenta no está activa o está bloqueada.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        
        if user.locked_until:
            user.locked_until = user.locked_until.replace(tzinfo=timezone.utc)
        
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            time_left = user.locked_until - datetime.now(timezone.utc)
            raise DomainException(
                message=f"La cuenta está bloqueada temporalmente. Intenta nuevamente en {time_left.seconds // 60} minutos.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if not verify_password(password, user.password):
            self.handle_failed_login_attempt(user)
        
        # Autenticación exitosa
        user.failed_attempts = 0
        user.locked_until = None
        self.user_repository.update_user(user)
        return user

    def handle_failed_login_attempt(self, user: UserInDB) -> None:        
        maxFailedAttempts = 5
        lockOutTime = timedelta(minutes=5)
        
        user.failed_attempts += 1
        
        if user.failed_attempts >= maxFailedAttempts:
            user.locked_until = datetime.now(timezone.utc) + lockOutTime
            user.state_id = self.user_repository.get_locked_user_state_id()  # Estado bloqueado
            self.user_repository.update_user(user)
            raise DomainException(
                message=f"La cuenta ha sido bloqueada debido a múltiples intentos fallidos. Intenta nuevamente después de {lockOutTime.seconds // 60} minutos.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        
        self.user_repository.update_user(user)
        raise DomainException(
            message="Contraseña incorrecta",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    def unlock_user(self, user: UserInDB):
        current_time = datetime.now(timezone.utc)
        
        if user.locked_until:
            user.locked_until = user.locked_until.replace(tzinfo=timezone.utc)
        
        if user.locked_until and current_time > user.locked_until:
            user.failed_attempts = 0
            user.locked_until = None
            user.state_id = self.user_repository.get_active_user_state_id()  # Estado activo
            self.user_repository.update_user(user)

    def initiate_two_factor_auth(self, user: UserInDB) -> bool:
        try:
            # Eliminar cualquier verificación anterior
            self.user_repository.delete_two_factor_verification(user.id)
            
            # Generar el PIN y su hash
            pin, pin_hash = generate_pin()
            
            # Crear un nuevo registro de verificación
            verification = VerificacionDospasos(
                usuario_id=user.id,
                pin=pin_hash,
                expiracion=datetime.now(timezone.utc) + timedelta(minutes=5)
            )
            
            # Enviar el PIN al correo electrónico del usuario
            if self.send_two_factor_pin(user.email, pin):
                self.user_repository.add_two_factor_verification(verification)
                return True
            else:
                return False
        except Exception as e:
            print(f"Error al iniciar la verificación en dos pasos: {str(e)}")
            return False

    def send_two_factor_pin(self, email: str, pin: str):
        subject = "Código de verificación en dos pasos - AgroInSight"
        text_content = f"Tu código de verificación en dos pasos es: {pin}\nEste código expirará en 10 minutos."
        html_content = f"<html><body><p><strong>Tu código de verificación en dos pasos es: {pin}</strong></p><p>Este código expirará en 10 minutos.</p></body></html>"
        
        return send_email(email, subject, text_content, html_content)