"""
Módulo para el caso de uso de confirmación del PIN de recuperación de contraseña.

Este módulo contiene la clase ConfirmRecoveryPinUseCase que maneja la lógica
para confirmar el PIN de recuperación de contraseña enviado al usuario.
"""

from sqlalchemy.orm import Session
from fastapi import status
from datetime import timedelta
from app.infrastructure.common.response_models import SuccessResponse
from app.user.application.services.user_state_validator import UserState, UserStateValidator
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException, UserHasBeenBlockedException, UserNotRegisteredException
from app.user.application.services.user_service import UserService

class ConfirmRecoveryPinUseCase:
    """
    Caso de uso para confirmar el PIN de recuperación de contraseña.

    Esta clase maneja el proceso de confirmación del PIN de recuperación,
    incluyendo la validación del estado del usuario, la verificación del PIN,
    y el manejo de intentos fallidos.

    Attributes:
        db (Session): Sesión de base de datos para operaciones de persistencia.
        user_repository (UserRepository): Repositorio para operaciones relacionadas con usuarios.
        state_validator (UserStateValidator): Validador del estado del usuario.
    """

    def __init__(self, db: Session):
        """
        Inicializa una nueva instancia de ConfirmRecoveryPinUseCase.

        Args:
            db (Session): Sesión de base de datos para operaciones de persistencia.
        """
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)
        self.user_service = UserService(db)
        
    def confirm_recovery(self, email: str, pin: str) -> SuccessResponse:
        """
        Confirma el PIN de recuperación de contraseña.

        Este método valida el estado del usuario, verifica la existencia de una solicitud
        de recuperación de contraseña válida, comprueba el PIN proporcionado y maneja
        los intentos fallidos.

        Args:
            email (str): Correo electrónico del usuario.
            pin (str): PIN de recuperación proporcionado por el usuario.

        Returns:
            SuccessResponse: Respuesta indicando que el PIN se confirmó correctamente.

        Raises:
            UserNotRegisteredException: Si el usuario no está registrado.
            DomainException: Si no hay una solicitud de recuperación válida, el PIN ha expirado,
                             el PIN es incorrecto, o hay otros errores.
            UserHasBeenBlockedException: Si el usuario ha sido bloqueado debido a múltiples intentos fallidos.
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

        recovery = self.user_service.get_last(user.recuperacion_contrasena)
        if not recovery:
            raise DomainException(
                message="No hay un registro de recuperación de contraseña pendiente.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        if self.user_service.is_expired(recovery):
            self.user_repository.delete_password_recovery(recovery)
            raise DomainException(
                message="La recuperación de contraseña ha expirado. Por favor, inicie el proceso de recuperación de contraseña nuevamente.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        recovery_pin = self.user_service.verify_pin(recovery, pin)
        
        if not recovery_pin:
            attempts = self.user_service.increment_attempts(recovery)
            
            if attempts >= 3:
                block_time = 10
                self.user_repository.delete_password_recovery(recovery)
                self.user_service.block_user(user, timedelta(minutes=block_time))
                raise UserHasBeenBlockedException(block_time)
                
            raise DomainException(
                message="PIN de recuperación incorrecto.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        recovery.pin_confirmado = True
        self.user_repository.update_password_recovery(recovery)
        
        return SuccessResponse(
                message="PIN de recuperación confirmado correctamente."
            )
