from sqlalchemy.orm import Session
from fastapi import status
from datetime import datetime, timedelta, timezone
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.services.email_service import send_email
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException

class ResendRecoveryUseCase:
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
            
        # Verificar si la cuenta del usuario está pendiente de confirmación
        pending_state_id = self.user_repository.get_pending_user_state_id()
        if user.state_id == pending_state_id:
            raise DomainException(
                message="Tu cuenta está pendiente de confirmación. Por favor, confirma tu registro.",
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
                return {"message": "Se ha reenviado el PIN de recuperación a tu correo electrónico."}
            else:
                raise DomainException(
                    message="No se pudo reenviar el PIN de recuperación a tu correo electrónico.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            raise DomainException(
                message=f"Error al reenviar el PIN de recuperación de contraseña: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def send_password_recovery_email(self, email: str, pin: str) -> bool:
        subject = "Reenvío: Recuperación de contraseña - AgroInSight"
        text_content = f"Reenvío: Tu PIN de recuperación de contraseña es: {pin}\nEste PIN expirará en 10 minutos."
        html_content = f"""
        <html>
            <body>
                <p><strong>Reenvío: Tu PIN de recuperación de contraseña es: {pin}</strong></p>
                <p>Este PIN expirará en 10 minutos.</p>
            </body>
        </html>
        """
        
        return send_email(email, subject, text_content, html_content)