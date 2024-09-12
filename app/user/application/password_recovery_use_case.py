from sqlalchemy.orm import Session
from app.user.infrastructure.user_orm_model import User
from app.user.infrastructure.password_recovery_orm_model import RecuperacionContrasena
from app.core.security.security_utils import hash_password, verify_password
from app.core.services.email_service import send_password_recovery_email
from datetime import datetime, timedelta
import secrets
import hashlib

class PasswordRecoveryUseCase:
    def __init__(self, db: Session):
        self.db = db

    def initiate_password_recovery(self, email: str) -> bool:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return False

        # Eliminar recuperaciones anteriores si existen
        self.db.query(RecuperacionContrasena).filter(RecuperacionContrasena.usuario_id == user.id).delete()

        pin = ''.join(secrets.choice('0123456789') for _ in range(4))
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()

        recovery = RecuperacionContrasena(
            usuario_id=user.id,
            pin=pin_hash,
            expiracion=datetime.utcnow() + timedelta(minutes=10)
        )
        self.db.add(recovery)
        self.db.commit()

        return send_password_recovery_email(email, pin)

    def resend_recovery_pin(self, email: str) -> bool:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return False

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
        self.db.commit()

        return send_password_recovery_email(email, pin)

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

        # Verificar que la nueva contraseña no sea igual a la anterior
        if verify_password(new_password, user.password):
            return False  # La nueva contraseña es igual a la anterior

        user.password = hash_password(new_password)
        self.db.delete(recovery)
        self.db.commit()

        return True