from sqlalchemy.orm import Session
from fastapi import status
from datetime import datetime, timedelta, timezone
from app.core.services.pin_service import generate_pin
from app.user.infrastructure.orm_models import RecuperacionContrasena
from app.core.services.email_service import send_email
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.exceptions import DomainException

class ResendRecoveryUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def resend_recovery_pin(self, email: str) -> bool:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise DomainException(
                message="Email no registrado.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        try:
            recovery = self.user_repository.get_password_recovery(user.id)

            if not recovery:
                # Si no hay un registro de recuperación válido, levantar un error
                raise DomainException(
                    message="No hay una recuperación de contraseña pendiente",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Generar un nuevo PIN y su hash
            pin, pin_hash = generate_pin()

            if self.send_password_recovery_email(email, pin):
                recovery.pin = pin_hash
                recovery.expiracion = datetime.now(timezone.utc) + timedelta(minutes=10)
                recovery.intentos = 0
                self.user_repository.update_password_recovery(recovery)
                return {"message": "Se ha reenviado el código de recuperación a tu correo electrónico."}
            else:
                raise DomainException(
                    message="No se pudo reenviar el código de recuperación a tu correo electrónico.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            raise DomainException(
                message=f"Error al reenviar el codigop de recuperación de contraseña: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def send_password_recovery_email(self, email: str, pin: str) -> bool:
        subject = "Reenvío: Recuperación de contraseña - AgroInSight"
        text_content = f"Reenvío: Tu código de recuperación de contraseña es: {pin}\nEste código expirará en 10 minutos."
        html_content = f"""
        <html>
            <body>
                <p><strong>Reenvío: Tu código de recuperación de contraseña es: {pin}</strong></p>
                <p>Este código expirará en 10 minutos.</p>
            </body>
        </html>
        """
        
        return send_email(email, subject, text_content, html_content)