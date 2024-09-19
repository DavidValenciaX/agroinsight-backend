from datetime import timedelta, datetime, timezone
from sqlalchemy.orm import Session
from app.user.infrastructure.orm_models import VerificacionDospasos
from app.user.infrastructure.sql_repository import UserRepository
from app.core.services.pin_service import generate_pin
from app.core.services.email_service import send_email

class Resend2faUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def resend_2fa_pin(self, email: str) -> bool:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            return False
        
        try:
            self.user_repository.delete_two_factor_verification(user.id)
            
            pin, pin_hash = generate_pin()
            
            verification = VerificacionDospasos(
                usuario_id=user.id,
                pin=pin_hash,
                expiracion=datetime.now(timezone.utc) + timedelta(minutes=5)
            )
            self.user_repository.add_two_factor_verification(verification)
            
            if self.send_two_factor_pin(user.email, pin):
                return True
            else:
                self.user_repository.delete_two_factor_verification(user.id)
                return False
        except Exception as e:
            print(f"Error al reenviar el PIN de doble verificación: {str(e)}")
            return False
        
    def send_two_factor_pin(self, email: str, pin: str):
        subject = "Reenvío de código de verificación en dos pasos - AgroInSight"
        text_content = f"Reenvío: Tu código de verificación en dos pasos es: {pin}\nEste código expirará en 5 minutos."
        html_content = f"<html><body><p><strong>Reenvío: Tu código de verificación en dos pasos es: {pin}</strong></p><p>Este código expirará en 5 minutos.</p></body></html>"
        
        return send_email(email, subject, text_content, html_content)