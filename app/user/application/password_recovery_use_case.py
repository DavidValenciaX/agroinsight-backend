from sqlalchemy.orm import Session
from fastapi import status
from datetime import datetime, timedelta, timezone
from app.core.services.pin_service import generate_pin, hash_pin
from app.user.infrastructure.orm_models import RecuperacionContrasena
from app.core.security.security_utils import hash_password, verify_password
from app.core.services.email_service import send_email
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.exceptions import TooManyRecoveryAttempts, DomainException

class PasswordRecoveryUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def execute(self, email: str) -> dict:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise DomainException(
                message="Este correo no está registrado, regístrese en la aplicación por favor.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        try:
            self.user_repository.delete_password_recovery(user.id)

            pin, pin_hash = generate_pin()

            recovery = RecuperacionContrasena(
                usuario_id=user.id,
                pin=pin_hash,
                expiracion=datetime.now(timezone.utc) + timedelta(minutes=10)
            )
            
            if self.send_password_recovery_email(email, pin):
                self.user_repository.add_password_recovery(recovery)
                return {"message": "Se ha enviado un código de recuperación a tu correo electrónico."}
            else:
                raise DomainException(
                    message="No se pudo reenviar el código de recuperación a tu correo electrónico.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            raise DomainException(
                message=f"Error en el proceso la recuperación de contraseña: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def send_password_recovery_email(self, email: str, pin: str) -> bool:
        subject = "Recuperación de contraseña - AgroInSight"
        text_content = f"Tu código de recuperación de contraseña es: {pin}\nEste código expirará en 10 minutos."
        html_content = f"<html><body><p><strong>Tu código de recuperación de contraseña es: {pin}</strong></p><p>Este código expirará en 10 minutos.</p></body></html>"
        
        return send_email(email, subject, text_content, html_content)

    def confirm_recovery_pin(self, email: str, pin: str) -> bool:
        """Confirma el PIN de recuperación de contraseña."""
        user = self.user_repository.get_user_by_email(email)
        if not user:
            return False

        recovery = self.user_repository.get_password_recovery(user.id)
        if not recovery:
            return False

        # Verificar si el PIN proporcionado coincide
        pin_hash = hash_pin(pin)
        if pin_hash == recovery.pin:
            # PIN correcto, eliminar el registro de recuperación
            return True
        else:
            # PIN incorrecto, incrementar los intentos
            recovery.intentos += 1
            if recovery.intentos >= 3:
                self.handle_failed_recovery_confirmation(user.id)
            else:
                self.user_repository.add_password_recovery(recovery)
            return False
        
    def handle_failed_recovery_confirmation(self, user_id: int):
        """Maneja el bloqueo del usuario tras demasiados intentos fallidos de confirmación de recuperación."""
        self.user_repository.delete_password_recovery(user_id)
        locked = self.user_repository.block_user(user_id, timedelta(minutes=10))
        if locked:
            raise TooManyRecoveryAttempts()
        else:
            raise Exception("No se pudo bloquear al usuario debido a un error interno.")

    def reset_password(self, email: str, new_password: str) -> bool:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            return False

        recovery = self.user_repository.get_password_recovery(user.id)

        if not recovery:
            return False

        if verify_password(new_password, user.password):
            return False

        user.password = hash_password(new_password)
        self.user_repository.delete_recovery(recovery)

        return True