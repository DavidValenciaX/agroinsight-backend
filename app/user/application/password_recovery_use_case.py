from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import hashlib
from app.user.infrastructure.orm_models.password_recovery_orm_model import RecuperacionContrasena
from app.core.security.security_utils import hash_password, verify_password
from app.core.services.email_service import send_email
from app.user.infrastructure.repositories.sql_user_repository import UserRepository

class PasswordRecoveryUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def initiate_password_recovery(self, email: str) -> bool:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            return False

        try:
            self.user_repository.delete_password_recovery(user.id)

            pin = ''.join(secrets.choice('0123456789') for _ in range(4))
            pin_hash = hashlib.sha256(pin.encode()).hexdigest()

            recovery = RecuperacionContrasena(
                usuario_id=user.id,
                pin=pin_hash,
                expiracion=datetime.utcnow() + timedelta(minutes=10)
            )
            
            if self.send_password_recovery_email(email, pin):
                self.user_repository.add_password_recovery(recovery)
                return True
            else:
                return False
        except Exception as e:
            print(f"Error al iniciar la recuperación de contraseña: {str(e)}")
            return False
    
    def send_password_recovery_email(self, email: str, pin: str) -> bool:
        subject = "Recuperación de contraseña - AgroInSight"
        text_content = f"Tu código de recuperación de contraseña es: {pin}\nEste código expirará en 10 minutos."
        html_content = f"<html><body><p><strong>Tu código de recuperación de contraseña es: {pin}</strong></p><p>Este código expirará en 10 minutos.</p></body></html>"
        
        return send_email(email, subject, text_content, html_content)

    def resend_recovery_pin(self, email: str) -> bool:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            return False

        try:
            recovery = self.user_repository.get_password_recovery(user.id)

            if not recovery:
                # Si no hay un registro de recuperación válido, iniciar uno nuevo
                return self.initiate_password_recovery(email)

            # Generar un nuevo PIN y su hash
            pin = ''.join(secrets.choice('0123456789') for _ in range(4))
            pin_hash = hashlib.sha256(pin.encode()).hexdigest()

            if self.send_password_recovery_email(email, pin):
                recovery.pin = pin_hash
                recovery.expiracion = datetime.utcnow() + timedelta(minutes=15)
                recovery.intentos = 0
                self.user_repository.add_password_recovery(recovery)
                return True
            else:
                return False
        except Exception as e:
            print(f"Error al reenviar el PIN de recuperación: {str(e)}")
            return False

    def confirm_recovery_pin(self, email: str, pin_hash: str) -> bool:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            return False

        recovery = self.user_repository.get_password_recovery_with_pin(user.id, pin_hash)
        if not recovery:
            return False

        # Aumentar el contador de intentos
        recovery.intentos += 1
        self.user_repository.add_password_recovery(recovery)

        # Si el número de intentos supera el límite, eliminar el registro de recuperación
        if recovery.intentos >= 3:
            self.user_repository.delete_recovery(recovery)
            return False

        return True

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