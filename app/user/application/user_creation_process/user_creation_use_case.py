from sqlalchemy.orm import Session
from fastapi import status
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.user.infrastructure.orm_models import User, ConfirmacionUsuario
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserCreate
from app.infrastructure.security.security_utils import hash_password
from app.infrastructure.common.common_exceptions import DomainException, UserStateException
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.services.email_service import send_email
from datetime import datetime, timezone, timedelta

class UserCreationUseCase:
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
        self.state_validator = UserStateValidator(self.user_repository)

    def execute(self, user_data: UserCreate) -> SuccessResponse:
        """
        Ejecuta el proceso de creación de un nuevo usuario.

        Este método realiza las siguientes operaciones:
        
        1. Verifica si el usuario ya existe.
        2. Valida el estado del usuario si ya existe.
        3. Crea un nuevo usuario con estado pendiente.
        4. Asigna el rol de usuario no confirmado.
        5. Crea y envía una confirmación por correo electrónico.

        Parameters:
            user_data (UserCreate): Datos del usuario a crear.

        Returns:
            SuccessResponse: Respuesta indicando el éxito de la operación.

        Raises:
            DomainException: Si ocurre un error durante el proceso de creación.
            UserStateException: Si el estado del usuario no es válido.
        """
        user = self.user_repository.get_user_by_email(user_data.email)
        
        if user:

            state_validation_result = self.state_validator.validate_user_state(
                user,
                disallowed_states=[UserState.ACTIVE, UserState.PENDING, UserState.INACTIVE, UserState.LOCKED]
            )
            if state_validation_result:
                return state_validation_result

        # Hash del password
        hashed_password = hash_password(user_data.password)

        # Obtener estado "pendiente" del usuario
        pending_state_id = self.user_repository.get_pending_user_state_id()
        if not pending_state_id:
            raise UserStateException(
                message="No se pudo encontrar el estado de usuario pendiente.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                user_state="unknown"
            )

        # Obtener rol "no confirmado"
        unconfirmed_role = self.user_repository.get_unconfirmed_user_role()
        if not unconfirmed_role:
            raise DomainException(
                message="No se pudo encontrar el rol de Usuario No Confirmado.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Crear nuevo usuario
        new_user = User(
            nombre=user_data.nombre,
            apellido=user_data.apellido,
            email=user_data.email,
            password=hashed_password,
            state_id=pending_state_id
        )
        created_user = self.user_repository.create_user(new_user)
            
        if not self.user_repository.assign_role_to_user(created_user.id, unconfirmed_role.id):
            self.user_repository.delete_user(created_user)  # Eliminar el usuario si falla la asignación del rol
            raise DomainException(
                message="No se pudo asignar el rol de Usuario No Confirmado.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Intentar crear la confirmación y enviar el correo
        if not self.create_and_send_confirmation(created_user):
            # Si falla la confirmación, eliminar el usuario
            self.user_repository.delete_user(created_user)
            raise DomainException(
                message="Error al crear la confirmación de usuario.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            
        return SuccessResponse(
                message="Usuario creado. Por favor, revisa tu email para confirmar el registro."
            )

    def create_and_send_confirmation(self, user: User) -> bool:
        """
        Crea y envía una confirmación de registro al usuario.

        Este método genera un PIN de confirmación, crea un registro de confirmación
        en la base de datos y envía un correo electrónico con el PIN al usuario.

        Parameters:
            user (User): El usuario para el cual se crea la confirmación.

        Returns:
            bool: True si la confirmación se creó y envió correctamente, False en caso contrario.
        """
        try:
            # Generar PIN y su hash
            expiration_time = 10  # minutos
            pin, pin_hash = generate_pin()
            confirmation = ConfirmacionUsuario(
                usuario_id=user.id,
                pin=pin_hash,
                expiracion=datetime.now(timezone.utc) + timedelta(minutes=expiration_time)
            )

            # Enviar correo de confirmación y agregar la confirmación al repositorio
            if not self.send_confirmation_email(user.email, pin):
                return False
            return self.user_repository.add_user_confirmation(confirmation)
        except Exception as e:
            print(f"Error al crear la confirmación del usuario: {str(e)}")
            return False

    def send_confirmation_email(self, email: str, pin: str) -> bool:
        """
        Envía un correo electrónico de confirmación al usuario.

        Parameters:
            email (str): La dirección de correo electrónico del usuario.
            pin (str): El PIN de confirmación generado.

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