from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import hashlib
from app.user.infrastructure.orm_models.user_orm_model import User
from app.user.infrastructure.orm_models.password_recovery_orm_model import RecuperacionContrasena
from app.core.security.security_utils import hash_password, verify_password
from app.core.services.email_service import send_email

class PasswordRecoveryUseCase:
    def __init__(self, db: Session):
        self.db = db

    def initiate_password_recovery(self, email: str) -> bool:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return False

        try:
            self.db.begin_nested()
            self.db.query(RecuperacionContrasena).filter(RecuperacionContrasena.usuario_id == user.id).delete()

            pin = ''.join(secrets.choice('0123456789') for _ in range(4))
            pin_hash = hashlib.sha256(pin.encode()).hexdigest()

            recovery = RecuperacionContrasena(
                usuario_id=user.id,
                pin=pin_hash,
                expiracion=datetime.utcnow() + timedelta(minutes=10)
            )
            self.db.add(recovery)

            if self.send_password_recovery_email(email, pin):
                self.db.commit()
                return True
            else:
                self.db.rollback()
                return False
        except Exception as e:
            self.db.rollback()
            print(f"Error al iniciar la recuperación de contraseña: {str(e)}")
            return False
    
    def send_password_recovery_email(self, email: str, pin: str) -> bool:
        subject = "Recuperación de contraseña - AgroInSight"
        text_content = f"Tu código de recuperación de contraseña es: {pin}\nEste código expirará en 10 minutos."
        html_content = f"<html><body><p><strong>Tu código de recuperación de contraseña es: {pin}</strong></p><p>Este código expirará en 10 minutos.</p></body></html>"
        
        return send_email(email, subject, text_content, html_content)

    def resend_recovery_pin(self, email: str) -> bool:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return False

        try:
            self.db.begin_nested()
            recovery = self.db.query(RecuperacionContrasena).filter(
                RecuperacionContrasena.usuario_id == user.id,
                RecuperacionContrasena.expiracion > datetime.utcnow()
            ).first()

            if not recovery:
                return self.initiate_password_recovery(email)

            pin = ''.join(secrets.choice('0123456789') for _ in range(4))
            pin_hash = hashlib.sha256(pin.encode()).hexdigest()

            recovery.pin = pin_hash
            recovery.expiracion = datetime.utcnow() + timedelta(minutes=15)
            recovery.intentos = 0

            if self.send_password_recovery_email(email, pin):
                self.db.commit()
                return True
            else:
                self.db.rollback()
                return False
        except Exception as e:
            self.db.rollback()
            print(f"Error al reenviar el PIN de recuperación: {str(e)}")
            return False

    def confirm_recovery_pin(self, email: str, pin_hash: str) -> bool:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return False

        recovery = self.db.query(RecuperacionContrasena).filter(
            RecuperacionContrasena.usuario_id == user.id,
            RecuperacionContrasena.pin == pin_hash,
            RecuperacionContrasena.expiracion > datetime.utcnow()
        ).first()

        if not recovery:
            return False

        recovery.intentos += 1
        self.db.commit()

        if recovery.intentos >= 3:
            self.db.delete(recovery)
            self.db.commit()
            return False

        return True

    def reset_password(self, email: str, new_password: str) -> bool:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return False

        recovery = self.db.query(RecuperacionContrasena).filter(
            RecuperacionContrasena.usuario_id == user.id,
            RecuperacionContrasena.expiracion > datetime.utcnow()
        ).first()

        if not recovery:
            return False

        if verify_password(new_password, user.password):
            return False

        user.password = hash_password(new_password)
        self.db.delete(recovery)
        self.db.commit()

        return True