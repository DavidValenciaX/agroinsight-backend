from datetime import timedelta, datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks, status
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.user.infrastructure.orm_models import UserConfirmation
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.services.email_service import send_email
from app.infrastructure.common.datetime_utils import ensure_utc, datetime_utc_time

class ResendConfirmationUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)

    def resend_confirmation(self, email: str, background_tasks: BackgroundTasks) -> SuccessResponse:
        user = self.user_repository.get_user_with_confirmation(email)
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

        # Obtener confirmación del usuario
        confirmation = self.get_last_confirmation(user.confirmacion)

        # Verificar si hay una confirmación pendiente
        if not confirmation:
            raise DomainException(
                message="No hay una confirmación pendiente para reenviar el PIN.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Definimos el tiempo de espera en minutos
        warning_time = 3

        # Si es el primer reenvío (resends == 0), permitir sin restricción
        if confirmation.resends > 0:
            # Si ya ha reenviado al menos una vez, verificar si han pasado 3 minutos
            if self.was_recently_requested(confirmation, warning_time):
                raise DomainException(
                    message=f"Ya has solicitado un PIN recientemente. Por favor, espera {warning_time} minutos antes de solicitar uno nuevo.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )

        # Generar nuevo PIN y su hash
        pin, pin_hash = generate_pin()
        
        expiration_time = 10  # minutos
        expiration_datetime = datetime_utc_time() + timedelta(minutes=expiration_time)
        
        # Actualizar el registro de confirmación de usuario con manejo de errores
        confirmation.pin = pin_hash
        confirmation.expiracion = expiration_datetime
        confirmation.resends += 1
        confirmation.intentos = 0
        confirmation.created_at = datetime_utc_time()
        
        if not self.user_repository.update_user_confirmation(confirmation):
            # Log the error or handle it as needed
            raise DomainException(
                message="Error al actualizar la confirmación del usuario",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Enviar el correo electrónico con el nuevo PIN
        background_tasks.add_task(self.resend_confirmation_email, email, pin)
        
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
    
    def was_recently_requested(self, confirmation: UserConfirmation, minutes: int = 3) -> bool:
        """Verifica si la verificación de confirmación se solicitó hace menos de x minutos."""
        return (datetime_utc_time() - ensure_utc(confirmation.created_at)).total_seconds() < minutes * 60
    
    def get_last_confirmation(self, confirmation: UserConfirmation) -> Optional[UserConfirmation]:
        """Obtiene la última confirmación del usuario."""
        if isinstance(confirmation, list) and confirmation:
            # Ordenar las confirmaciones por fecha de creación de forma ascendente
            confirmation.sort(key=lambda c: c.created_at)
            # Tomar el último registro
            latest_confirmation = confirmation[-1]
            # Eliminar todas las confirmaciones anteriores a la última
            for old_confirmation in confirmation[:-1]:
                self.user_repository.delete_user_confirmation(old_confirmation)
            # Actualizar la variable confirmation para solo trabajar con la última
            return latest_confirmation
        # Si no hay confirmaciones, retornar None
        return None