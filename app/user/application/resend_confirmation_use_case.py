from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app.user.infrastructure.orm_models import ConfirmacionUsuario
from app.core.services.pin_service import generate_pin
from app.core.services.email_service import send_email
from app.user.infrastructure.sql_repository import UserRepository

class ResendConfirmationUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

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
                expiracion=datetime.now(timezone.utc) + timedelta(minutes=10)
            )
                
            # Intentar enviar el correo electrónico
            if self.resend_confirmation_email(email, pin):
                self.user_repository.add_user_confirmation(confirmation)
                return True
            else:
                return False
        except Exception as e:
            # Manejar excepción
            print(f"Error al reenviar el PIN de confirmación: {str(e)}")
            return False

    def resend_confirmation_email(self, email: str, pin: str) -> bool:
        """Envía un correo electrónico con el PIN de confirmación."""
        subject = "Confirma tu registro en AgroInSight"
        text_content = f"Reenvío: Tu PIN de confirmación es: {pin}\nEste PIN expirará en 10 minutos."
        html_content = f"""
        <html>
            <body>
                <p><strong>Reenvío: Tu PIN de confirmación es: {pin}</strong></p>
                <p>Este PIN expirará en 10 minutos.</p>
            </body>
        </html>
        """
        return send_email(email, subject, text_content, html_content)