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
    """
    Caso de uso para reenviar el PIN de recuperación de contraseña.

    Esta clase maneja el proceso de reenvío del PIN de recuperación, incluyendo
    la validación del estado del usuario, la verificación de solicitudes recientes,
    y la generación y envío de un nuevo PIN.

    Attributes:
        db (Session): Sesión de base de datos para operaciones de persistencia.
        user_repository (UserRepository): Repositorio para operaciones relacionadas con usuarios.
        state_validator (UserStateValidator): Validador del estado del usuario.
    """

    def __init__(self, db: Session):
        """
        Inicializa una nueva instancia de ResendRecoveryUseCase.

        Args:
            db (Session): Sesión de base de datos para operaciones de persistencia.
        """
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)

    def resend_recovery(self, email: str, background_tasks: BackgroundTasks) -> SuccessResponse:
        """
        Reenvía el PIN de recuperación de contraseña.

        Este método valida el estado del usuario, verifica si se ha solicitado recientemente
        un reenvío, genera un nuevo PIN y lo envía por correo electrónico.

        Args:
            email (str): Correo electrónico del usuario que solicita el reenvío.
            background_tasks (BackgroundTasks): Tareas en segundo plano para enviar el correo.

        Returns:
            SuccessResponse: Respuesta indicando que se ha reenviado el PIN de recuperación.

        Raises:
            UserNotRegisteredException: Si el usuario no está registrado.
            DomainException: Si no hay un registro de recuperación pendiente, se ha solicitado
                             un reenvío recientemente, o hay otros errores.
        """
        user = self.user_repository.get_user_with_password_recovery(email)
        if not user:
            raise UserNotRegisteredException()
        
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

        warning_time = 3

        if recovery.resends > 0:
            if self.was_recently_requested(recovery, warning_time):
                raise DomainException(
                    message=f"Ya has solicitado un PIN de recuperación recientemente. Por favor, espera {warning_time} minutos antes de solicitar uno nuevo.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )

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
        """
        Envía un correo electrónico con el PIN de recuperación de contraseña reenviado.

        Args:
            email (str): Dirección de correo electrónico del destinatario.
            pin (str): PIN de recuperación generado.

        Returns:
            bool: True si el correo se envió exitosamente, False en caso contrario.
        """
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
        """
        Verifica si la recuperación de contraseña se solicitó recientemente.

        Args:
            recovery (PasswordRecovery): Objeto de recuperación de contraseña.
            minutes (int, optional): Número de minutos para considerar una solicitud reciente. Por defecto es 3.

        Returns:
            bool: True si la solicitud fue reciente, False en caso contrario.
        """
        return (datetime_utc_time() - ensure_utc(recovery.created_at)).total_seconds() < minutes * 60
    
    def get_last_password_recovery(self, recovery: PasswordRecovery) -> Optional[PasswordRecovery]:
        """
        Obtiene la última recuperación de contraseña del usuario.

        Esta función también elimina todas las recuperaciones anteriores a la última.

        Args:
            recovery (PasswordRecovery): Objeto o lista de objetos de recuperación de contraseña.

        Returns:
            Optional[PasswordRecovery]: La última recuperación de contraseña, o None si no hay ninguna.
        """
        if isinstance(recovery, list) and recovery:
            recovery.sort(key=lambda r: r.created_at)
            latest_recovery = recovery[-1]
            for old_recovery in recovery[:-1]:
                self.user_repository.delete_password_recovery(old_recovery)
            return latest_recovery
        return None
