from typing import Optional
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks, status
from datetime import datetime, timedelta, timezone
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.services.email_service import send_email
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.user.infrastructure.orm_models import PasswordRecovery
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException
from app.infrastructure.common.datetime_utils import ensure_utc, datetime_utc_time

class ResendRecoveryUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)

    def resend_recovery(self, email: str, background_tasks: BackgroundTasks) -> SuccessResponse:
        user = self.user_repository.get_user_with_password_recovery(email)
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

        recovery = self.get_last_password_recovery(user.recuperacion_contrasena)

        if not recovery:
            raise DomainException(
                message="No hay un registro de recuperación de contraseña pendiente.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Definimos el tiempo de espera en minutos
        warning_time = 3

        # Si es el primer reenvío (resends == 0), permitir sin restricción
        if recovery.resends > 0:
            # Verificar si ya se ha enviado un PIN en los últimos 3 minutos
            if self.was_recently_requested(recovery, warning_time):
                raise DomainException(
                    message=f"Ya has solicitado un PIN de recuperación recientemente. Por favor, espera {warning_time} minutos antes de solicitar uno nuevo.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )

        # Generar un nuevo PIN y su hash
        pin, pin_hash = generate_pin()

        background_tasks.add_task(self.send_password_recovery_email, email, pin)
        
        recovery.pin = pin_hash
        recovery.expiracion = datetime_utc_time() + timedelta(minutes=10)
        recovery.intentos = 0
        recovery.resends += 1
        self.user_repository.update_password_recovery(recovery)
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
    
    def was_recently_requested(self, recovery: PasswordRecovery, minutes: int = 3) -> bool:
        """Verifica si la recuperación de contraseña se solicitó hace menos de x minutos."""
        return (datetime_utc_time() - ensure_utc(recovery.created_at)).total_seconds() < minutes * 60
    
    def get_last_password_recovery(self, recovery: PasswordRecovery) -> Optional[PasswordRecovery]:
        """Obtiene la última recuperación de contraseña del usuario."""
        if isinstance(recovery, list) and recovery:
            # Ordenar las recuperaciones por fecha de creación de forma ascendente
            recovery.sort(key=lambda r: r.created_at)
            # Tomar el último registro
            latest_recovery = recovery[-1]
            # Eliminar todas las recuperaciones anteriores a la última
            for old_recovery in recovery[:-1]:
                self.user_repository.delete_password_recovery(old_recovery)
            # Actualizar la variable recovery para solo trabajar con la última
            return latest_recovery
        # Si no hay recuperaciones, retornar None
        return None