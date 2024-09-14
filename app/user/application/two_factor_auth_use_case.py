from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.user.infrastructure.orm_models.two_factor_verify_orm_model import VerificacionDospasos
from app.user.infrastructure.orm_models.user_orm_model import User
from app.core.services.pin_service import generate_pin
from app.core.services.email_service import send_email
import hashlib

class TwoFactorAuthUseCase:
    def __init__(self, db: Session):
        self.db = db

    def initiate_two_factor_auth(self, user: User) -> bool:
        return self.create_two_factor_verification(self.db, user)
    
    def create_two_factor_verification(self, db: Session, user: User) -> bool:
        try:
            db.query(VerificacionDospasos).filter(VerificacionDospasos.usuario_id == user.id).delete()
            
            pin, pin_hash = generate_pin()
            
            verification = VerificacionDospasos(
                usuario_id=user.id,
                pin=pin_hash,
                expiracion=datetime.utcnow() + timedelta(minutes=5)
            )
            db.add(verification)
            
            if self.send_two_factor_pin(user.email, pin):
                db.commit()
                return True
            else:
                db.rollback()
                return False
        except Exception as e:
            db.rollback()
            print(f"Error al crear la verificación en dos pasos: {str(e)}")
            return False
        
    def send_two_factor_pin(self, email: str, pin: str):
        subject = "Código de verificación en dos pasos - AgroInSight"
        text_content = f"Tu código de verificación en dos pasos es: {pin}\nEste código expirará en 5 minutos."
        html_content = f"<html><body><p><strong>Tu código de verificación en dos pasos es: {pin}</strong></p><p>Este código expirará en 5 minutos.</p></body></html>"
        
        return send_email(email, subject, text_content, html_content)

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
    
    def resend_2fa_pin(self, email: str) -> bool:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return False
        
        try:
            
            # Iniciar una transacción
            self.db.begin_nested()
            # Eliminar la verificación existente si la hay
            self.db.query(VerificacionDospasos).filter(VerificacionDospasos.usuario_id == user.id).delete()
            
            # Crear una nueva verificación
            pin, pin_hash = generate_pin()
            
            verification = VerificacionDospasos(
                usuario_id=user.id,
                pin=pin_hash,
                expiracion=datetime.utcnow() + timedelta(minutes=5)
            )
            self.db.add(verification)
            
            if self.send_two_factor_pin(user.email, pin):
                self.db.commit()
                return True
            else:
                self.db.rollback()
                return False
        except Exception as e:
            self.db.rollback()
            print(f"Error al reenviar el PIN de doble verificación: {str(e)}")
            return False

    def handle_failed_verification(self, user_id: int):
        verification = self.db.query(VerificacionDospasos).filter(VerificacionDospasos.usuario_id == user_id).first()
        if verification:
            verification.intentos += 1
            if verification.intentos >= 3:
                user = self.db.query(User).filter(User.id == user_id).first()
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                user.state_id = 3  # Estado bloqueado
                self.db.delete(verification)
            self.db.commit()