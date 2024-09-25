from datetime import timedelta, datetime, timezone
from sqlalchemy.orm import Session
from fastapi import status
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.services.email_service import send_email
from app.user.infrastructure.orm_models import ConfirmacionUsuario


class ResendConfirmationUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def execute(self, email: str) -> dict:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise DomainException(
                message="Usuario no encontrado.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Verificar el estado del usuario
        active_state_id = self.user_repository.get_active_user_state_id()
        if user.state_id == active_state_id:
            raise DomainException(
                message="La cuenta ya está confirmada y activa.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Verificar si el usuario ha sido eliminado
        inactive_state_id = self.user_repository.get_inactive_user_state_id()
        if user.state_id == inactive_state_id:
            raise DomainException(
                message="El usuario fue eliminado del sistema.",
                status_code=status.HTTP_410_GONE
            )

        # Verificar si la cuenta del usuario está bloqueada        
        if user.locked_until:
            user.locked_until = user.locked_until.replace(tzinfo=timezone.utc)

        locked_state_id = self.user_repository.get_locked_user_state_id()
        if user.state_id == locked_state_id and user.locked_until > datetime.now(timezone.utc):
            time_left = user.locked_until - datetime.now(timezone.utc)
            minutos_restantes = time_left.seconds // 60
            raise DomainException(
                message=f"Tu cuenta está bloqueada. Intenta nuevamente en {minutos_restantes} minutos.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Verificar si hay una confirmación pendiente
        pending_confirmation = self.user_repository.get_user_pending_confirmation(user.id)
        if not pending_confirmation:
            raise DomainException(
                message="No hay una confirmación pendiente para reenviar el PIN.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

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
                return {"message":"PIN de confirmación reenviado con éxito."}
            else:
                raise DomainException(
                    message="No se pudo enviar el correo electrónico.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            # Manejar excepciones específicas si es necesario
            raise DomainException(
                message=f"Error al reenviar el PIN de confirmación: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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