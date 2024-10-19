from sqlalchemy.orm import Session
from fastapi import BackgroundTasks, status
from datetime import timedelta
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.user_state_validator import UserState
from app.user.infrastructure.orm_models import PasswordRecovery
from app.infrastructure.services.email_service import send_email
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.infrastructure.common.datetime_utils import datetime_utc_time
from app.user.services.user_service import UserService

class PasswordRecoveryUseCase:
    """
    Caso de uso para el proceso de recuperación de contraseña.

    Esta clase maneja el proceso de recuperación de contraseña, incluyendo la generación
    y envío de PIN, validación del estado del usuario y gestión de solicitudes recientes.

    Attributes:
        db (Session): Sesión de base de datos para operaciones de persistencia.
        user_repository (UserRepository): Repositorio para operaciones relacionadas con usuarios.
        state_validator (UserStateValidator): Validador del estado del usuario.
    """

    def __init__(self, db: Session):
        """
        Inicializa una nueva instancia de PasswordRecoveryUseCase.

        Args:
            db (Session): Sesión de base de datos para operaciones de persistencia.
        """
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)
        self.user_service = UserService(db)

    def recovery_password(self, email: str, background_tasks: BackgroundTasks) -> SuccessResponse:
        """
        Inicia el proceso de recuperación de contraseña para un usuario.

        Este método valida el estado del usuario, verifica si se ha solicitado recientemente
        un PIN, genera un nuevo PIN y lo envía por correo electrónico.

        Args:
            email (str): Correo electrónico del usuario que solicita la recuperación.
            background_tasks (BackgroundTasks): Tareas en segundo plano para enviar el correo.

        Returns:
            SuccessResponse: Respuesta indicando que se ha enviado el PIN de recuperación.

        Raises:
            UserNotRegisteredException: Si el usuario no está registrado.
            DomainException: Si se ha solicitado un PIN recientemente o hay otros errores.
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
        
        warning_time = 3
        recovery = self.user_service.get_last(user.recuperacion_contrasena)
        if recovery and self.user_service.is_recently_requested(recovery, warning_time):
            raise DomainException(
                message=f"Ya has solicitado un PIN de recuperación recientemente. Por favor, espera {warning_time} minutos antes de solicitar uno nuevo.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS
            )

        self.user_repository.delete_password_recovery(recovery)

        pin, pin_hash = generate_pin()
        
        expiration_datetime = self.user_service.expiration_time()

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
        """
        Envía un correo electrónico con el PIN de recuperación de contraseña.

        Args:
            email (str): Dirección de correo electrónico del destinatario.
            pin (str): PIN de recuperación generado.

        Returns:
            bool: True si el correo se envió exitosamente, False en caso contrario.
        """
        subject = "Recuperación de contraseña - AgroInSight"
        text_content = f"Tu PIN de recuperación de contraseña es: {pin}\nEste PIN expirará en 10 minutos."
        html_content = f"<html><body><p><strong>Tu PIN de recuperación de contraseña es: {pin}</strong></p><p>Este PIN expirará en 10 minutos.</p></body></html>"
        
        return send_email(email, subject, text_content, html_content)
