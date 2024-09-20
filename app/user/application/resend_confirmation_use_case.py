from sqlalchemy.orm import Session
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.exceptions import DomainException
from app.core.services.pin_service import generate_pin
from app.core.services.email_service import send_email
from app.user.infrastructure.orm_models import ConfirmacionUsuario
from datetime import datetime, timedelta, timezone

class ResendConfirmationUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def execute(self, email: str) -> str:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise DomainException(message="Usuario no encontrado.", status_code=404)
        
        # Verificar el estado del usuario
        active_state_id = self.user_repository.get_active_user_state_id()
        if user.state_id == active_state_id:
            raise DomainException(message="La cuenta ya está confirmada y activa.", status_code=400)
        
        # Verificar si hay una confirmación pendiente
        pending_confirmation = self.user_repository.get_user_pending_confirmation(user.id)
        if not pending_confirmation:
            raise DomainException(message="No hay una confirmación pendiente para reenviar el PIN.", status_code=400)
        
        try:
            # Eliminar confirmaciones existentes
            self.user_repository.delete_user_confirmations(user.id)
                
            # Generar nuevo PIN y su hash
            pin, pin_hash = generate_pin()
            confirmation = ConfirmacionUsuario(
                usuario_id=user.id,
                pin=pin_hash,
                expiracion=datetime.now(timezone.utc) + timedelta(minutes=10)
            )
                
            # Enviar el correo electrónico con el nuevo PIN
            if self.resend_confirmation_email(email, pin):
                self.user_repository.add_user_confirmation(confirmation)
                return "PIN de confirmación reenviado con éxito."
            else:
                raise DomainException(message="No se pudo enviar el correo electrónico.", status_code=500)
        except Exception as e:
            # Manejar excepciones específicas si es necesario
            raise DomainException(message=f"Error al reenviar el PIN de confirmación: {str(e)}", status_code=500)

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
