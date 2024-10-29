from sqlalchemy.orm import Session
from fastapi import BackgroundTasks, status
from app.user.application.services.user_service import UserService
from app.user.application.services.user_state_validator import UserState, UserStateValidator
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserCreate
from app.infrastructure.security.security_utils import hash_password
from app.infrastructure.common.common_exceptions import DomainException, UserStateException
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.services.email_service import send_email
from app.infrastructure.common.datetime_utils import datetime_utc_time

"""
Este módulo contiene la implementación del caso de uso para el registro de usuarios.

Incluye la clase UserRegisterUseCase que maneja la lógica de negocio para crear nuevos usuarios,
validar sus estados, y enviar correos de confirmación.
"""

class UserRegisterUseCase:
    """
    Caso de uso para la creación de un nuevo usuario en el sistema.

    Esta clase maneja la lógica de negocio para el registro de nuevos usuarios,
    incluyendo la validación de datos, la creación del usuario en la base de datos,
    y el envío de correos de confirmación.

    Attributes:
        db (Session): La sesión de base de datos para realizar operaciones.
        user_repository (UserRepository): Repositorio para operaciones de usuario.
        state_validator (UserStateValidator): Validador de estados de usuario.
    """

    def __init__(self, db: Session):
        """
        Inicializa una nueva instancia de UserRegisterUseCase.

        Args:
            db (Session): La sesión de base de datos a utilizar.
        """
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)
        self.user_service = UserService(db)

    def register_user(self, user_data: UserCreate, background_tasks: BackgroundTasks) -> SuccessResponse:
        """
        Crea un nuevo usuario en el sistema.

        Este método realiza las siguientes operaciones:
        1. Verifica si el usuario ya existe.
        2. Verifica si la confirmación del usuario ha expirado.
        3. Valida el estado del usuario si no tiene confirmación expirada.
        4. Crea un nuevo usuario con estado pendiente.
        5. Crea y envía una confirmación por correo electrónico.

        Args:
            user_data (UserCreate): Datos del usuario a crear.
            background_tasks (BackgroundTasks): Tareas en segundo plano para enviar el correo.

        Returns:
            SuccessResponse: Respuesta indicando el éxito de la operación.

        Raises:
            DomainException: Si ocurre un error durante el proceso de creación.
            UserStateException: Si el estado del usuario no es válido.
        """
        user = self.user_repository.get_user_with_confirmation(user_data.email)
        
        if user:
            confirmations = self.user_service.get_last(user.confirmacion)
            expired_confirmation = confirmations if confirmations and self.user_service.is_expired(confirmations) else None
            if expired_confirmation:
                self.user_repository.delete_user(user)
            else:
                state_validation_result = self.state_validator.validate_user_state(
                    user,
                    disallowed_states=[UserState.ACTIVE, UserState.PENDING, UserState.INACTIVE, UserState.LOCKED]
                )
                if state_validation_result:
                    return state_validation_result
        
        if not user_data.acepta_terminos:
            raise DomainException(
                message="Debes aceptar los términos y condiciones para registrarte.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Obtener estado "pendiente" del usuario (caché o consulta única)
        pending_state_id = self.user_service.get_user_state(self.user_service.PENDING_STATE_NAME).id
        if not pending_state_id:
            raise UserStateException(
                message="No se pudo encontrar el estado de usuario pendiente.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                user_state="unknown"
            )

        # Hash del password
        hashed_password = hash_password(user_data.password)

        user_data.password = hashed_password

        # Crear nuevo usuario
        created_user = self.user_repository.add_user(user_data, pending_state_id)
        
        # Generar PIN y su hash
        pin, pin_hash = generate_pin()
        
        expiration_datetime = self.user_service.expiration_time()
        
        if not self.user_repository.add_user_confirmation(user_id=created_user.id, pin_hash=pin_hash, expiration_datetime=expiration_datetime, created_at=datetime_utc_time()):
            raise DomainException(
                message="Error al agregar la confirmación del usuario.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Enviar correo de confirmación de manera asíncrona
        background_tasks.add_task(self.send_confirmation_email, created_user.email, pin)
    
        return SuccessResponse(
                message="Usuario creado. Por favor, revisa tu email para confirmar el registro."
            )

    def send_confirmation_email(self, email: str, pin: str) -> bool:
        """
        Envía un correo electrónico de confirmación al usuario.

        Args:
            email (str): Dirección de correo electrónico del usuario.
            pin (str): PIN de confirmación generado.

        Returns:
            bool: True si el correo se envió correctamente, False en caso contrario.
        """
        subject = "Confirma tu registro en AgroInSight"
        text_content = f"Tu PIN de confirmación es: {pin}\nEste PIN expirará en 10 minutos."
        html_content = f"""
        <html>
            <body>
                <p><strong>Tu PIN de confirmación es: {pin}</strong></p>
                <p>Este PIN expirará en 10 minutos.</p>
            </body>
        </html>
        """
        return send_email(email, subject, text_content, html_content)