"""
Este módulo contiene la implementación del caso de uso para la confirmación de registro de usuarios.

Incluye la clase ConfirmationUseCase que maneja la lógica de negocio para confirmar
el registro de usuarios mediante un PIN.
"""

from sqlalchemy.orm import Session
from fastapi import status
from app.infrastructure.common.response_models import SuccessResponse
from app.user.application.services.user_service import UserService
from app.user.domain.schemas import UserInDB
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException, UserStateException
from app.user.application.services.user_state_validator import UserState, UserStateValidator

class ConfirmationUseCase:
    """
    Caso de uso para la confirmación del registro de un usuario en el sistema.

    Esta clase maneja la lógica de negocio para confirmar el registro de usuarios,
    incluyendo la validación del PIN, la activación del usuario y la gestión de intentos fallidos.

    Attributes:
        db (Session): La sesión de base de datos para realizar operaciones.
        user_repository (UserRepository): Repositorio para operaciones de usuario.
        state_validator (UserStateValidator): Validador de estados de usuario.
    """

    def __init__(self, db: Session):
        """
        Inicializa una nueva instancia de ConfirmationUseCase.

        Args:
            db (Session): La sesión de base de datos a utilizar.
        """
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)
        self.user_service = UserService(db)
        
    def confirm_user(self, email: str, pin: str) -> SuccessResponse:
        """
        Confirma el registro de un usuario mediante un PIN.

        Este método realiza las siguientes operaciones:
        1. Obtiene el usuario por correo electrónico.
        2. Valida el estado del usuario.
        3. Verifica la existencia de una confirmación pendiente.
        4. Comprueba si la confirmación ha expirado.
        5. Verifica el PIN proporcionado.
        6. Activa el usuario si el PIN es correcto.
        7. Elimina el registro de confirmación.

        Args:
            email (str): Correo electrónico del usuario.
            pin (str): PIN de confirmación proporcionado por el usuario.

        Returns:
            SuccessResponse: Respuesta indicando el éxito de la operación.

        Raises:
            UserNotRegisteredException: Si el usuario no está registrado.
            DomainException: Si ocurre un error durante el proceso de confirmación.
            UserStateException: Si el estado del usuario no es válido.
        """
        # Obtener el usuario por correo electrónico
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
        
        # Verificar si hay una confirmación pendiente
        confirmation = self.user_service.get_last(user.confirmacion)
        if not confirmation:
            raise DomainException(
                message="No hay un registro de confirmación para este usuario.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Verificar si la confirmación está expirada
        if self.user_service.is_expired(confirmation):
            # Eliminar usuario y con el se elimina su confirmación
            self.user_repository.delete_user(user)
            raise DomainException(
                message="La confirmación ha expirado. Por favor, inicie el proceso de registro nuevamente.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        # Hashear el PIN proporcionado
        confirm_pin = self.user_service.verify_pin(confirmation, pin)
        
        if not confirm_pin:
            # Manejar intentos fallidos de confirmación
            intentos = self.user_service.increment_attempts(confirmation)
            if intentos >= 3:
                # Eliminar usuario y con el se elimina su confirmación
                self.user_repository.delete_user(user)
                raise DomainException(
                    message="Demasiados intentos. Por favor, inicie el proceso de registro nuevamente.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )
            raise DomainException(
                message="PIN de confirmación incorrecto.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
            
        self.activate_user(user)
        
        # Eliminar el registro de confirmación
        self.user_repository.delete_user_confirmation(confirmation)
        
        return SuccessResponse(
                message="Usuario confirmado exitosamente."
            )

    def activate_user(self, user: UserInDB) -> None:
        """
        Activa el usuario cambiando su estado a activo.

        Args:
            user (User): Objeto de usuario a activar.

        Raises:
            UserStateException: Si no se puede encontrar el estado de usuario activo.
        """
        active_state = self.user_service.get_user_state(self.user_service.ACTIVE_STATE_NAME)
        if not active_state:
            raise UserStateException(
                message="No se pudo encontrar el estado de usuario activo.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                user_state="unknown"
            )
        user.state_id = active_state.id
        self.user_repository.update_user(user)