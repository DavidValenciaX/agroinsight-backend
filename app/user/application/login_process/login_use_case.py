from datetime import timedelta
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks, status
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.response_models import SuccessResponse
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.services.email_service import send_email
from app.infrastructure.security.security_utils import verify_password
from app.infrastructure.common.common_exceptions import DomainException, UserHasBeenBlockedException, UserNotRegisteredException
from app.user.application.services.user_state_validator import UserState, UserStateValidator
from app.infrastructure.common.datetime_utils import datetime_utc_time
from app.user.application.services.user_service import UserService
from app.infrastructure.config.settings import WARNING_TIME

class LoginUseCase:
    """
    Caso de uso para el proceso de inicio de sesión.

    Esta clase maneja la lógica de negocio para el inicio de sesión de usuarios,
    incluyendo la validación de credenciales, el manejo de intentos fallidos,
    y la generación de PIN para autenticación de dos factores.

    Attributes:
        db (Session): La sesión de base de datos para realizar operaciones.
        user_repository (UserRepository): Repositorio para operaciones de usuario.
        state_validator (UserStateValidator): Validador de estados de usuario.
    """

    def __init__(self, db: Session):
        """
        Inicializa una nueva instancia de LoginUseCase.

        Args:
            db (Session): La sesión de base de datos a utilizar.
        """
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)
        self.user_service = UserService(db)
        
    def login_user(self, email: str, password: str, background_tasks: BackgroundTasks) -> SuccessResponse:
        """
        Inicia el proceso de inicio de sesión para un usuario.

        Este método realiza las siguientes operaciones:
        1. Verifica la existencia del usuario.
        2. Valida el estado del usuario.
        3. Verifica la contraseña.
        4. Maneja intentos fallidos de inicio de sesión.
        5. Genera y envía un PIN para autenticación de dos factores.

        Args:
            email (str): Correo electrónico del usuario.
            password (str): Contraseña del usuario.
            background_tasks (BackgroundTasks): Tareas en segundo plano para enviar el correo.

        Returns:
            SuccessResponse: Respuesta indicando el éxito del inicio del proceso de autenticación.

        Raises:
            UserNotRegisteredException: Si el usuario no está registrado.
            DomainException: Si ocurre un error durante el proceso de inicio de sesión.
            UserHasBeenBlockedException: Si el usuario ha sido bloqueado por múltiples intentos fallidos.
        """
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
        
        # Verificar si verification trajo una lista de varias verificaciones,
        verification = self.user_service.get_last(user.verificacion_dos_pasos)
            
        # Verificar si ya se ha enviado un PIN en los ltimos 3 minutos
        warning_time = WARNING_TIME

        if verification:
            if self.user_service.is_recently_requested(verification, warning_time):
                raise DomainException(
                    message=f"Ya has solicitado un PIN de autenticación recientemente. Por favor, espera {warning_time} minutos antes de solicitar uno nuevo.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            # Eliminar verificaciones de dos pasos expiradas
            self.user_repository.delete_two_factor_verification(verification)

        if not verify_password(password, user.password):
            self.handle_failed_login_attempt(user)
        
        # Autenticación exitosa
        user.failed_attempts = 0
        user.locked_until = None
        self.user_repository.update_user(user)
        
        # Generar el PIN y su hash
        pin, pin_hash = generate_pin()
        
        expiration_datetime = self.user_service.expiration_time()
        
        self.user_repository.add_two_factor_verification(user_id=user.id, pin_hash=pin_hash, expiration_datetime=expiration_datetime, created_at=datetime_utc_time())
        
        # Enviar el PIN al correo electrónico del usuario
        background_tasks.add_task(self.send_two_factor_verification_email, user.email, pin)

        return SuccessResponse(
            message="Verificación en dos pasos iniciada. Por favor, revisa tu correo electrónico para obtener el PIN."
        )

    def handle_failed_login_attempt(self, user: UserInDB) -> None:
        """
        Maneja un intento fallido de inicio de sesión.

        Incrementa el contador de intentos fallidos y bloquea al usuario si se excede el límite.

        Args:
            user (User): El usuario que ha fallado en el intento de inicio de sesión.

        Raises:
            UserHasBeenBlockedException: Si el usuario es bloqueado debido a múltiples intentos fallidos.
            DomainException: Si la contraseña es incorrecta pero no se ha alcanzado el límite de intentos.
        """
        max_failed_attempts = 3
        block_time = 10
        
        user.failed_attempts += 1
        self.user_repository.update_user(user)

        if user.failed_attempts >= max_failed_attempts:
            self.user_service.block_user(user, timedelta(minutes=block_time))
            raise UserHasBeenBlockedException(block_time)

        raise DomainException(
            message="Contraseña incorrecta.",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    def send_two_factor_verification_email(self, email: str, pin: str) -> bool:
        """
        Envía un correo electrónico con el PIN de verificación en dos pasos.

        Args:
            email (str): Dirección de correo electrónico del usuario.
            pin (str): PIN de verificación generado.

        Returns:
            bool: True si el correo se envió correctamente, False en caso contrario.
        """
        subject = "PIN de verificación en dos pasos - AgroInSight"
        text_content = f"Tu PIN de verificación en dos pasos es: {pin}\nEste PIN expirará en 10 minutos."
        html_content = f"<html><body><p><strong>Tu PIN de verificación en dos pasos es: {pin}</strong></p><p>Este PIN expirará en 10 minutos.</p></body></html>"
        
        return send_email(email, subject, text_content, html_content)