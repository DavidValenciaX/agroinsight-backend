from sqlalchemy.orm import Session
from fastapi import BackgroundTasks, status
from datetime import datetime, timedelta, timezone
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.user_state_validator import UserState
from app.user.infrastructure.orm_models import PasswordRecovery
from app.infrastructure.services.email_service import send_email
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.infrastructure.common.datetime_utils import ensure_utc, datetime_utc_time

class PasswordRecoveryUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)

    def recovery_password(self, email: str, background_tasks: BackgroundTasks) -> SuccessResponse:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise UserNotRegisteredException()
            
        # Eliminar recuperaciones de contraseña expiradas
        self.user_repository.delete_expired_password_recoveries(user.id)
        
        # Validar el estado del usuario
        state_validation_result = self.state_validator.validate_user_state(
            user,
            allowed_states=[UserState.ACTIVE],
            disallowed_states=[UserState.INACTIVE, UserState.PENDING, UserState.LOCKED]
        )
        if state_validation_result:
            return state_validation_result
        
        # Definimos el tiempo de espera en minutos
        warning_time = 3
            
        # Verificar si ya se ha enviado un PIN en los últimos 3 minutos
        last_recovery = self.user_repository.get_last_password_recovery(user.id)
        if last_recovery and (datetime_utc_time() - ensure_utc(last_recovery.created_at)).total_seconds() < warning_time * 60:
            raise DomainException(
                message=f"Ya has solicitado un PIN de recuperación recientemente. Por favor, espera {warning_time} minutos antes de solicitar uno nuevo.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS
            )

        self.user_repository.delete_password_recovery(user.id)

        pin, pin_hash = generate_pin()
        
        expiration_time = 10  # minutos
        expiration_datetime = datetime_utc_time() + timedelta(minutes=expiration_time)

        recovery = PasswordRecovery(
            usuario_id=user.id,
            pin=pin_hash,
            expiracion=expiration_datetime,
            resends=0,
            created_at=datetime_utc_time()
        )
        
        background_tasks.add_task(self.send_password_recovery_email, email, pin)
        
        self.user_repository.add_password_recovery(recovery)
        return SuccessResponse(
            message="Se ha enviado un PIN de recuperación a tu correo electrónico."
        )

    
    def send_password_recovery_email(self, email: str, pin: str) -> bool:
        subject = "Recuperación de contraseña - AgroInSight"
        text_content = f"Tu PIN de recuperación de contraseña es: {pin}\nEste PIN expirará en 10 minutos."
        html_content = f"<html><body><p><strong>Tu PIN de recuperación de contraseña es: {pin}</strong></p><p>Este PIN expirará en 10 minutos.</p></body></html>"
        
        return send_email(email, subject, text_content, html_content)
