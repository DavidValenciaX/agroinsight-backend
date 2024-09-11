from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.user.infrastructure.verificacion_dos_pasos_orm_model import VerificacionDospasos
from app.user.infrastructure.user_orm_model import User
from app.core.services.email_service import create_two_factor_verification
import hashlib

class TwoFactorAuthUseCase:
    def __init__(self, db: Session):
        self.db = db

    def initiate_two_factor_auth(self, user: User) -> bool:
        return create_two_factor_verification(self.db, user)

    def verify_two_factor_pin(self, user_id: int, pin: str) -> bool:
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        verification = self.db.query(VerificacionDospasos).filter(
            VerificacionDospasos.usuario_id == user_id,
            VerificacionDospasos.pin == pin_hash,
            VerificacionDospasos.expiracion > datetime.utcnow()
        ).first()

        if not verification:
            return False

        # Eliminar la verificación después de un uso exitoso
        self.db.delete(verification)
        self.db.commit()
        return True

    def handle_failed_verification(self, user_id: int):
        verification = self.db.query(VerificacionDospasos).filter(VerificacionDospasos.usuario_id == user_id).first()
        if verification:
            verification.intentos += 1
            if verification.intentos >= 3:
                # Si hay demasiados intentos fallidos, eliminar la verificación y bloquear al usuario
                user = self.db.query(User).filter(User.id == user_id).first()
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                self.db.delete(verification)
            self.db.commit()