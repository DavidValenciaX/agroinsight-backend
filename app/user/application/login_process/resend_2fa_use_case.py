"""
Módulo para el caso de uso de reenvío del PIN de verificación en dos pasos.

Este módulo contiene la clase Resend2faUseCase que maneja la lógica para reenviar
el PIN de verificación en dos pasos a un usuario.
"""

from datetime import timedelta, datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks, status
from app.infrastructure.common.response_models import SuccessResponse
from app.user.services.user_service import UserService
from app.user.infrastructure.orm_models import TwoStepVerification
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.services.email_service import send_email
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.infrastructure.common.datetime_utils import ensure_utc, datetime_utc_time

class Resend2faUseCase:
    """
    Caso de uso para reenviar el PIN de verificación en dos pasos.

    Esta clase maneja el proceso de reenvío del PIN de verificación en dos pasos,
    incluyendo la validación del estado del usuario, la verificación de solicitudes
    recientes, y la generación y envío de un nuevo PIN.

    Attributes:
        db (Session): Sesión de base de datos para operaciones de persistencia.
        user_repository (UserRepository): Repositorio para operaciones relacionadas con usuarios.
        state_validator (UserStateValidator): Validador del estado del usuario.
    """

    def __init__(self, db: Session):
        """
        Inicializa una nueva instancia de Resend2faUseCase.

        Args:
            db (Session): Sesión de base de datos para operaciones de persistencia.
        """
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)
        self.user_service = UserService(db)
        
    def resend_2fa(self, email: str, background_tasks: BackgroundTasks) -> SuccessResponse:
        """
        Reenvía el PIN de verificación en dos pasos.

        Este método valida el estado del usuario, verifica si se ha solicitado recientemente
        un reenvío, genera un nuevo PIN y lo envía por correo electrónico.

        Args:
            email (str): Correo electrónico del usuario que solicita el reenvío.
            background_tasks (BackgroundTasks): Tareas en segundo plano para enviar el correo.

        Returns:
            SuccessResponse: Respuesta indicando que se ha reenviado el PIN de verificación.

        Raises:
            UserNotRegisteredException: Si el usuario no está registrado.
            DomainException: Si no hay una verificación pendiente, se ha solicitado
                             un reenvío recientemente, o hay otros errores.
        """
        user = self.user_repository.get_user_with_two_factor_verification(email)
        if not user:
            raise UserNotRegisteredException()
        
        state_validation_result = self.state_validator.validate_user_state(
            user,
            allowed_states=[UserState.ACTIVE],
            disallowed_states=[UserState.INACTIVE, UserState.PENDING, UserState.LOCKED]
        )
        if state_validation_result:
            return state_validation_result
        
        verification = self.user_service.get_last(user.verificacion_dos_pasos)
        if not verification:
            raise DomainException(
                message="No hay una verificación de doble factor de autenticación pendiente para reenviar el PIN.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        warning_time = 3
        
        if verification.resends > 0:
            if self.user_service.is_recently_requested(verification, warning_time):
                raise DomainException(
                    message=f"Ya has solicitado un PIN de autenticación recientemente. Por favor, espera {warning_time} minutos antes de solicitar uno nuevo.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )
        
        pin, pin_hash = generate_pin()
        
        expiration_datetime = self.user_service.expiration_time()
        
        verification.pin = pin_hash
        verification.expiracion = expiration_datetime
        verification.resends += 1
        verification.intentos = 0
        verification.created_at = datetime_utc_time()
        
        if not self.user_repository.update_two_factor_verification(verification):
            raise DomainException(
                message="No se pudo actualizar la verificación de doble factor de autenticación",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        background_tasks.add_task(self.send_two_factor_pin, user.email, pin)

        return SuccessResponse(
            message="PIN de verificación en dos pasos reenviado con éxito."
        )
        
    def send_two_factor_pin(self, email: str, pin: str) -> bool:
        """
        Envía un correo electrónico con el PIN de verificación en dos pasos reenviado.

        Args:
            email (str): Dirección de correo electrónico del destinatario.
            pin (str): PIN de verificación generado.

        Returns:
            bool: True si el correo se envió exitosamente, False en caso contrario.
        """
        subject = "Reenvío de PIN de verificación en dos pasos - AgroInSight"
        text_content = f"Reenvío: Tu PIN de verificación en dos pasos es: {pin}\nEste PIN expirará en 10 minutos."
        html_content = f"""
        <html>
            <body>
                <p><strong>Reenvío: Tu PIN de verificación en dos pasos es: {pin}</strong></p>
                <p>Este PIN expirará en 10 minutos.</p>
            </body>
        </html>
        """
        
        return send_email(email, subject, text_content, html_content)
