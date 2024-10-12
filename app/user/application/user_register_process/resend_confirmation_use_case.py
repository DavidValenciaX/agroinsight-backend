from datetime import timedelta, datetime, timezone
from sqlalchemy.orm import Session
from fastapi import status
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.services.email_service import send_email
from app.infrastructure.common.datetime_utils import ensure_utc

class ResendConfirmationUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)

    def resend_confirmation(self, email: str) -> SuccessResponse:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise UserNotRegisteredException()

        # Validar el estado del usuario
        state_validation_result = self.state_validator.validate_user_state(
            user,
            allowed_states=[UserState.PENDING],
            disallowed_states=[UserState.ACTIVE, UserState.LOCKED, UserState.INACTIVE]
        )
        if state_validation_result:
            return state_validation_result

        # Obtener la última confirmación del usuario
        last_confirmation = self.user_repository.get_last_user_confirmation(user.id)

        # Verificar si hay una confirmación pendiente
        if not last_confirmation:
            raise DomainException(
                message="No hay una confirmación pendiente para reenviar el PIN.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Si es el primer reenvío (resends == 0), permitir sin restricción
        if last_confirmation.resends > 0:
            # Si ya ha reenviado al menos una vez, verificar si han pasado 3 minutos
            time_since_last_send = (datetime.now(timezone.utc) - ensure_utc(last_confirmation.created_at)).total_seconds()
            if time_since_last_send < 180:
                raise DomainException(
                    message="Ya has solicitado un PIN recientemente. Por favor, espera 3 minutos antes de solicitar uno nuevo.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )

        # Generar nuevo PIN y su hash
        pin, pin_hash = generate_pin()
        
        # Actualizar el registro de confirmación de usuario con manejo de errores
        last_confirmation.pin = pin_hash
        last_confirmation.expiracion = datetime.now(timezone.utc) + timedelta(minutes=10)
        last_confirmation.resends += 1
        last_confirmation.intentos = 0
        
        if not self.user_repository.update_user_confirmation(last_confirmation):
            # Log the error or handle it as needed
            raise DomainException(
                message="Error al actualizar la confirmación del usuario",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Enviar el correo electrónico con el nuevo PIN
        if not self.resend_confirmation_email(email, pin):
            raise DomainException(
                message="Error al reenviar el correo de confirmación.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return SuccessResponse(
            message="PIN de confirmación reenviado con éxito."
        )

    def resend_confirmation_email(self, email: str, pin: str) -> bool:
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
