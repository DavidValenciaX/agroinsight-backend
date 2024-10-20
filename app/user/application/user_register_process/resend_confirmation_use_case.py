"""
Este módulo contiene la implementación del caso de uso para reenviar la confirmación de registro de usuarios.

Incluye la clase ResendConfirmationUseCase que maneja la lógica de negocio para reenviar PINs de confirmación
a usuarios que están en proceso de registro.
"""

from sqlalchemy.orm import Session
from fastapi import BackgroundTasks, status
from app.infrastructure.common.response_models import SuccessResponse
from app.user.application.services.user_state_validator import UserState, UserStateValidator
from app.user.infrastructure.sql_repository import UserRepository
from app.user.application.services.user_service import UserService
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.services.email_service import send_email
from app.infrastructure.common.datetime_utils import datetime_utc_time

class ResendConfirmationUseCase:
    """
    Caso de uso para reenviar la confirmación de registro a un usuario.

    Esta clase maneja la lógica de negocio para reenviar PINs de confirmación,
    incluyendo la validación del estado del usuario, la generación de nuevos PINs,
    y el envío de correos electrónicos de confirmación.

    Attributes:
        db (Session): La sesión de base de datos para realizar operaciones.
        user_repository (UserRepository): Repositorio para operaciones de usuario.
        state_validator (UserStateValidator): Validador de estados de usuario.
    """

    def __init__(self, db: Session):
        """
        Inicializa una nueva instancia de ResendConfirmationUseCase.

        Args:
            db (Session): La sesión de base de datos a utilizar.
        """
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)
        self.user_service = UserService(db)

    def resend_confirmation(self, email: str, background_tasks: BackgroundTasks) -> SuccessResponse:
        """
        Reenvía la confirmación de registro a un usuario.

        Este método realiza las siguientes operaciones:
        1. Verifica si el usuario existe.
        2. Valida el estado del usuario.
        3. Obtiene la última confirmación del usuario.
        4. Verifica si se puede reenviar la confirmación (tiempo de espera).
        5. Genera un nuevo PIN y actualiza la confirmación.
        6. Envía un nuevo correo electrónico con el PIN.

        Args:
            email (str): Correo electrónico del usuario.
            background_tasks (BackgroundTasks): Tareas en segundo plano para enviar el correo.

        Returns:
            SuccessResponse: Respuesta indicando el éxito de la operación.

        Raises:
            UserNotRegisteredException: Si el usuario no está registrado.
            DomainException: Si ocurre un error durante el proceso de reenvío.
        """
        user = self.user_repository.get_user_with_confirmation(email)
        if not user:
            raise UserNotRegisteredException()

        # Validar el estado del usuario
        state_validation_result = self.state_validator.validate_user_state(
            user,
            allowed_states=[UserState.PENDING],
            disallowed_states=[UserState.ACTIVE, UserState.LOCKED, UserState.INACTIVE]
        )
        if state_validation_result:
            return state_validation_result

        # Obtener confirmación del usuario
        confirmation = self.user_service.get_last(user.confirmacion)

        # Verificar si hay una confirmación pendiente
        if not confirmation:
            raise DomainException(
                message="No hay una confirmación pendiente para reenviar el PIN.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Definimos el tiempo de espera en minutos
        warning_time = 3

        # Si es el primer reenvío (resends == 0), permitir sin restricción
        if confirmation.resends > 0:
            # Si ya ha reenviado al menos una vez, verificar si han pasado 3 minutos
            if self.user_service.is_recently_requested(confirmation, warning_time):
                raise DomainException(
                    message=f"Ya has solicitado un PIN recientemente. Por favor, espera {warning_time} minutos antes de solicitar uno nuevo.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )

        # Generar nuevo PIN y su hash
        pin, pin_hash = generate_pin()
        
        expiration_datetime = self.user_service.expiration_time()
        
        # Actualizar el registro de confirmación de usuario con manejo de errores
        confirmation.pin = pin_hash
        confirmation.expiracion = expiration_datetime
        confirmation.resends += 1
        confirmation.intentos = 0
        confirmation.created_at = datetime_utc_time()
        
        if not self.user_repository.update_user_confirmation(confirmation):
            # Log the error or handle it as needed
            raise DomainException(
                message="Error al actualizar la confirmación del usuario",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Enviar el correo electrónico con el nuevo PIN
        background_tasks.add_task(self.resend_confirmation_email, email, pin)
        
        return SuccessResponse(
            message="PIN de confirmación reenviado con éxito."
        )

    def resend_confirmation_email(self, email: str, pin: str) -> bool:
        """
        Envía un correo electrónico con el PIN de confirmación reenviado.

        Args:
            email (str): Dirección de correo electrónico del usuario.
            pin (str): Nuevo PIN de confirmación generado.

        Returns:
            bool: True si el correo se envió correctamente, False en caso contrario.
        """
        subject = "Confirma tu registro en AgroInSight"
        text_content = f"Reenvío: Tu PIN de confirmación es: {pin}\nEste PIN expirará en 10 minutos."
        html_content = f"""
        <html>
            <body>
                <p><strong>Reenvío: Tu PIN de confirmación es: {pin}</strong></p>
                <p>Este PIN expirará en 10 minutos.</p>
            </body>
        </html>
        """
        return send_email(email, subject, text_content, html_content)
