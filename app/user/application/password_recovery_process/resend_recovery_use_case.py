from sqlalchemy.orm import Session
from fastapi import status
from datetime import datetime, timedelta, timezone
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.services.email_service import send_email
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException
from app.infrastructure.common.datetime_utils import ensure_utc

class ResendRecoveryUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(self.user_repository)

    def execute(self, email: str) -> SuccessResponse:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise UserNotRegisteredException()
            
        # Validar el estado del usuario
        state_validation_result = self.state_validator.validate_user_state(
            user,
            allowed_states=[UserState.ACTIVE],
            disallowed_states=[UserState.INACTIVE, UserState.PENDING, UserState.LOCKED]
        )
        if state_validation_result:
            return state_validation_result

        last_recovery = self.user_repository.get_last_password_recovery(user.id)

        if not last_recovery:
            raise DomainException(
                message="No hay un registro de recuperación de contraseña pendiente.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Si es el primer reenvío (resends == 0), permitir sin restricción
        if last_recovery.resends > 0:
            # Verificar si ya se ha enviado un PIN en los últimos 3 minutos
            if (datetime.now(timezone.utc) - ensure_utc(last_recovery.created_at)).total_seconds() < 180:
                raise DomainException(
                    message="Ya has solicitado un PIN de recuperación recientemente. Por favor, espera 3 minutos antes de solicitar uno nuevo.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )

        # Generar un nuevo PIN y su hash
        pin, pin_hash = generate_pin()

        if not self.send_password_recovery_email(email, pin):
            raise DomainException(
                message="No se pudo reenviar el PIN de recuperación a tu correo electrónico.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        last_recovery.pin = pin_hash
        last_recovery.expiracion = datetime.now(timezone.utc) + timedelta(minutes=10)
        last_recovery.intentos = 0
        last_recovery.resends += 1
        self.user_repository.update_password_recovery(last_recovery)
        return SuccessResponse(
            message="Se ha reenviado el PIN de recuperación a tu correo electrónico."
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