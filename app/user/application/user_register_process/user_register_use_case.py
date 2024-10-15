import pytz
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks, status
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.user.infrastructure.orm_models import User, UserConfirmation
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserCreate
from app.infrastructure.security.security_utils import hash_password
from app.infrastructure.common.common_exceptions import DomainException, UserStateException
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.services.email_service import send_email
from datetime import datetime, timezone, timedelta
from app.infrastructure.common.datetime_utils import datetime_utc_time

class UserRegisterUseCase:
    """
    Caso de uso para la creación de un nuevo usuario en el sistema.

    Esta clase maneja la lógica de negocio para el registro de nuevos usuarios,
    incluyendo la validación de datos, la creación del usuario en la base de datos,
    y el envío de correos de confirmación.

    Attributes:
    ----------
        - db (Session): La sesión de base de datos para realizar operaciones.
        - user_repository (UserRepository): Repositorio para operaciones de usuario.
        - state_validator (UserStateValidator): Validador de estados de usuario.
    """
    def __init__(self, db: Session):
        """
        Inicializa una nueva instancia de UserCreationUseCase.

        Parameters:
        -------
            - db (Session): La sesión de base de datos a utilizar.
        """
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)

    def register_user(self, user_data: UserCreate, background_tasks: BackgroundTasks) -> SuccessResponse:
        """
        Crea al nuevo usuario.

        Este método realiza las siguientes operaciones:
        
        1. Verificar si el usuario ya existe.
        2. Verificar si la confirmación del usuario ha expirado.
        3. Validar el estado del usuario si no tiene confirmación expirada.
        4. Crea un nuevo usuario con estado pendiente.
        5. Asigna el rol de rol no confirmado.
        6. Crea y envía una confirmación por correo electrónico.

        Parameters:
            user_data (UserCreate): Datos del usuario a crear.

        Returns:
            SuccessResponse: Respuesta indicando el éxito de la operación.

        Raises:
            DomainException: Si ocurre un error durante el proceso de creación.
            UserStateException: Si el estado del usuario no es válido.
        """

        user = self.user_repository.get_user_with_confirmation(user_data.email)
        
        if user:
            expired_confirmation = user.confirmacion if user.confirmacion and self._is_confirmation_expired(user.confirmacion) else None
            if expired_confirmation:
                self.user_repository.delete_user(user)
            else:
                state_validation_result = self.state_validator.validate_user_state(
                    user,
                    disallowed_states=[UserState.ACTIVE, UserState.PENDING, UserState.INACTIVE, UserState.LOCKED]
                )
                if state_validation_result:
                    return state_validation_result

        # Obtener estado "pendiente" del usuario (caché o consulta única)
        pending_state_id = self.user_repository.get_pending_user_state_id()
        if not pending_state_id:
            raise UserStateException(
                message="No se pudo encontrar el estado de usuario pendiente.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                user_state="unknown"
            )

        # Hash del password
        hashed_password = hash_password(user_data.password)

        # Crear nuevo usuario
        new_user = User(
            nombre=user_data.nombre,
            apellido=user_data.apellido,
            email=user_data.email,
            password=hashed_password,
            state_id=pending_state_id
        )
        created_user = self.user_repository.register_user(new_user)
        
        # Generar PIN y su hash
        pin, pin_hash = generate_pin()
        
        expiration_time = 10  # minutos
        expiration_datetime = datetime_utc_time() + timedelta(minutes=expiration_time)

        confirmation = UserConfirmation(
            usuario_id=created_user.id,
            pin=pin_hash,
            expiracion=expiration_datetime,
            resends=0,
            created_at=datetime_utc_time()
        )
        
        result = self.user_repository.add_user_confirmation(confirmation)
        if not result:
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
    
    def _is_confirmation_expired(self, confirmation: UserConfirmation) -> bool:
        """Verifica si la confirmación ha expirado."""
        return confirmation.expiracion < datetime_utc_time()