from datetime import timedelta, datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks, status
from app.infrastructure.common.response_models import SuccessResponse
from app.user.infrastructure.orm_models import TwoStepVerification
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.services.email_service import send_email
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.infrastructure.common.datetime_utils import ensure_utc, datetime_utc_time

class Resend2faUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)
        
    def resend_2fa(self, email: str, background_tasks: BackgroundTasks) -> SuccessResponse:
        user = self.user_repository.get_user_with_two_factor_verification(email)
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
        
        # Verificar si hay una verificación pendiente
        verification = self.get_last_verification(user.verificacion_dos_pasos)
        if not verification:
            raise DomainException(
                message="No hay una verificación de doble factor de autenticación pendiente para reenviar el PIN.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Definimos el tiempo de espera en minutos
        warning_time = 3
        
        # Si es el primer reenvío (resends == 0), permitir sin restricción
        if verification.resends > 0:
            # Verificar si ya se ha enviado un PIN en los últimos 3 minutos
            if self.was_recently_requested(verification, warning_time):
                raise DomainException(
                    message=f"Ya has solicitado un PIN de autenticación recientemente. Por favor, espera {warning_time} minutos antes de solicitar uno nuevo.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )
        
        # Generar un nuevo PIN y su hash
        pin, pin_hash = generate_pin()
        
        expiration_time = 10  # minutos
        expiration_datetime = datetime_utc_time() + timedelta(minutes=expiration_time)
        
        # Actualizar el registro existente de verificación de dos pasos
        verification.pin = pin_hash
        verification.expiracion = expiration_datetime
        verification.resends += 1
        verification.intentos = 0
        verification.created_at = datetime_utc_time()
        
        if not self.user_repository.update_two_factor_verification(verification):
            raise DomainException(
                message="No se pudo actualizar la verificación de doble factor de autenticación",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Enviar el PIN al correo electrónico del usuario
        background_tasks.add_task(self.send_two_factor_pin, user.email, pin)

        return SuccessResponse(
            message="PIN de verificación en dos pasos reenviado con éxito."
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
    
    def was_recently_requested(self, verification: TwoStepVerification, minutes: int = 3) -> bool:
        """Verifica si la verificación de dos pasos se solicitó hace menos de x minutos."""
        return (datetime_utc_time() - ensure_utc(verification.created_at)).total_seconds() < minutes * 60
    
    def get_last_verification(self, verification: TwoStepVerification) -> Optional[TwoStepVerification]:
        """Obtiene la última verificación de dos pasos si existe."""
        if isinstance(verification, list) and verification:
            # Ordenar las verificaciones por fecha de creación de forma ascendente
            verification.sort(key=lambda v: v.created_at)
            # Tomar el último registro
            latest_verification = verification[-1]
            # Eliminar todas las verificaciones anteriores a la última
            for old_verification in verification[:-1]:
                self.user_repository.delete_two_factor_verification(old_verification)
            # Actualizar la variable verification para solo trabajar con la última
            return latest_verification
        # Si no hay verificaciones, retornar None
        return None