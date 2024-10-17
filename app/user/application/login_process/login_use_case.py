from datetime import timedelta, datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks, status
from app.user.infrastructure.orm_models import TwoStepVerification, User
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserInDB
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.services.email_service import send_email
from app.infrastructure.security.security_utils import verify_password
from app.infrastructure.common.common_exceptions import DomainException, UserHasBeenBlockedException, UserNotRegisteredException
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.infrastructure.common.datetime_utils import ensure_utc, datetime_utc_time
from app.user.infrastructure.orm_models import UserState as UserStateModel
# Constantes para roles
ADMIN_ROLE_NAME = "Administrador de Finca"
WORKER_ROLE_NAME = "Trabajador Agrícola"

# Constantes para estados
ACTIVE_STATE_NAME = "active"
LOCKED_STATE_NAME = "locked"
PENDING_STATE_NAME = "pending"
INACTIVE_STATE_NAME = "inactive"

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
        verification = self.get_last_verification(user.verificacion_dos_pasos)
            
        # Verificar si ya se ha enviado un PIN en los ltimos 3 minutos
        warning_time = 3

        if verification:
            if self.was_recently_requested(verification, warning_time):
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
        
        expiration_time = 10  # minutos
        expiration_datetime = datetime_utc_time() + timedelta(minutes=expiration_time)
        
        # Crear un nuevo registro de verificación
        verification = TwoStepVerification(
            usuario_id=user.id,
            pin=pin_hash,
            expiracion=expiration_datetime,
            resends=0,
            created_at=datetime_utc_time()
        )
        
        self.user_repository.add_two_factor_verification(verification)
        
        # Enviar el PIN al correo electrónico del usuario
        background_tasks.add_task(self.send_two_factor_verification_email, user.email, pin)

        return SuccessResponse(
            message="Verificación en dos pasos iniciada. Por favor, revisa tu correo electrónico para obtener el PIN."
        )

    def handle_failed_login_attempt(self, user: User) -> None:
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
            self.block_user(user, timedelta(minutes=block_time))
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
    
    def was_recently_requested(self, verification: TwoStepVerification, minutes: int = 3) -> bool:
        """
        Verifica si la verificación de dos pasos se solicitó recientemente.

        Args:
            verification (TwoStepVerification): Objeto de verificación de dos pasos.
            minutes (int, optional): Número de minutos para considerar como reciente. Por defecto es 3.

        Returns:
            bool: True si la verificación se solicitó hace menos de los minutos especificados, False en caso contrario.
        """
        """Verifica si la verificación de dos pasos se solicitó hace menos de x minutos."""
        return (datetime_utc_time() - ensure_utc(verification.created_at)).total_seconds() < minutes * 60
    
    def get_last_verification(self, verification: TwoStepVerification) -> Optional[TwoStepVerification]:
        """
        Obtiene la última verificación de dos pasos si existe.

        Args:
            verification (TwoStepVerification): Lista de verificaciones de dos pasos.

        Returns:
            Optional[TwoStepVerification]: La última verificación de dos pasos o None si no hay verificaciones.
        """
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
    
    def is_user_blocked(self, user: User) -> bool:
        """
        Verifica si un usuario está bloqueado.

        Args:
            user (User): El usuario a verificar.

        Returns:
            bool: True si el usuario está bloqueado, False en caso contrario.
        """
        return user.locked_until and datetime_utc_time() < user.locked_until and user.state_id == self.get_locked_user_state().id

    def block_user(self, user: User, lock_duration: timedelta) -> bool:
        """
        Bloquea a un usuario por un período de tiempo específico.

        Args:
            user (User): El usuario a bloquear.
            lock_duration (timedelta): Duración del bloqueo.

        Returns:
            bool: True si el usuario fue bloqueado exitosamente, False en caso contrario.

        Raises:
            DomainException: Si ocurre un error al bloquear al usuario.
        """
        try:
            user.locked_until = datetime_utc_time() + lock_duration
            user.state_id = self.get_locked_user_state().id
            if not self.user_repository.update_user(user):
                raise DomainException(
                    message="No se pudo actualizar el estado del usuario.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Verificación adicional
            if not self.is_user_blocked(user):
                raise DomainException(
                    message="No se pudo bloquear el usuario.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return True
        except Exception as e:
            raise DomainException(
                message=f"Error al bloquear el usuario: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_locked_user_state(self) -> Optional[UserStateModel]:
        """
        Obtiene el estado de usuario 'bloqueado'.

        Returns:
            Optional[UserStateModel]: El estado de usuario 'bloqueado'.

        Raises:
            DomainException: Si no se puede obtener el estado de usuario bloqueado.
        """
        locked_state = self.user_repository.get_state_by_name(LOCKED_STATE_NAME)
        if not locked_state:
            raise DomainException(
                message="No se pudo obtener el estado de usuario bloqueado.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return locked_state
