from datetime import timedelta, datetime, timezone
from sqlalchemy.orm import Session
from fastapi import status
from app.infrastructure.common.response_models import SuccessResponse
from app.user.infrastructure.orm_models import VerificacionDospasos
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.services.email_service import send_email
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.infrastructure.common.datetime_utils import ensure_utc
class Resend2faUseCase:
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
        
        # Verificar si hay una confirmación pendiente
        last_verification = self.user_repository.get_last_two_factor_verification(user.id)
        if not last_verification:
            raise DomainException(
                message="No hay una verificación de doble factor de autenticación pendiente para reenviar el PIN.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Si es el primer reenvío (resends == 0), permitir sin restricción
        if last_verification.resends > 0:
            # Verificar si ya se ha enviado un PIN en los últimos 3 minutos
            if (datetime.now(timezone.utc) - ensure_utc(last_verification.created_at)).total_seconds() < 180:
                raise DomainException(
                    message="Ya has solicitado un PIN de autenticación recientemente. Por favor, espera 3 minutos antes de solicitar uno nuevo.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )
        
        try:
            # Generar un nuevo PIN y su hash
            pin, pin_hash = generate_pin()
            
            # Actualizar el registro existente de verificación de dos pasos
            last_verification.pin = pin_hash
            last_verification.expiracion = datetime.now(timezone.utc) + timedelta(minutes=10)
            last_verification.resends += 1
            last_verification.intentos = 0
            self.user_repository.update_two_factor_verification(last_verification)
            
            # Enviar el PIN al correo electrónico del usuario
            if not self.send_two_factor_pin(user.email, pin):
                raise DomainException(
                    message="No se pudo reenviar el PIN. Verifique el correo electrónico o intenta más tarde.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return SuccessResponse(
                message="PIN de verificación en dos pasos reenviado con éxito."
            )

        except Exception as e:
            raise DomainException(
                message=f"Error al reenviar el PIN de doble verificación: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def send_two_factor_pin(self, email: str, pin: str) -> bool:
        subject = "Reenvío de PIN de verificación en dos pasos - AgroInSight"
        text_content = f"Reenvío: Tu PIN de verificación en dos pasos es: {pin}\nEste PIN expirará en 10 minutos."
        html_content = f"""
        <html>
            <body>
                <p><strong>Reenvío: Tu PIN de verificación en dos pasos es: {pin}</strong></p>
                <p>Este PIN expirará en 10 minutos.</p>
            </body>
        </html>
        """
        
        return send_email(email, subject, text_content, html_content)