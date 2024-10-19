"""
Módulo para el caso de uso de verificación de autenticación de dos factores.

Este módulo contiene la clase VerifyUseCase que maneja la lógica para verificar
el PIN de autenticación de dos factores proporcionado por el usuario.
"""

from datetime import timedelta
from sqlalchemy.orm import Session
from fastapi import status
from app.user.domain.schemas import TokenResponse
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.security.security_utils import create_access_token
from app.infrastructure.common.common_exceptions import DomainException, UserHasBeenBlockedException, UserNotRegisteredException
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.user.services.user_service import UserService

class VerifyUseCase:
    """
    Caso de uso para verificar la autenticación de dos factores.

    Esta clase maneja el proceso de verificación del PIN de autenticación de dos factores,
    incluyendo la validación del estado del usuario, la verificación del PIN,
    y el manejo de intentos fallidos.

    Attributes:
        db (Session): Sesión de base de datos para operaciones de persistencia.
        user_repository (UserRepository): Repositorio para operaciones relacionadas con usuarios.
        state_validator (UserStateValidator): Validador del estado del usuario.
    """

    def __init__(self, db: Session):
        """
        Inicializa una nueva instancia de VerifyUseCase.

        Args:
            db (Session): Sesión de base de datos para operaciones de persistencia.
        """
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)
        self.user_service = UserService(db)
        
    def verify_2fa(self, email: str, pin: str) -> TokenResponse:
        """
        Verifica el PIN de autenticación de dos factores.

        Este método valida el estado del usuario, verifica la existencia de una solicitud
        de verificación de dos factores válida, comprueba el PIN proporcionado y maneja
        los intentos fallidos.

        Args:
            email (str): Correo electrónico del usuario.
            pin (str): PIN de verificación proporcionado por el usuario.

        Returns:
            TokenResponse: Respuesta con el token de acceso si la verificación es exitosa.

        Raises:
            UserNotRegisteredException: Si el usuario no está registrado.
            DomainException: Si no hay una verificación pendiente, el PIN ha expirado,
                             el PIN es incorrecto, o hay otros errores.
            UserHasBeenBlockedException: Si el usuario ha sido bloqueado debido a múltiples intentos fallidos.
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
            
        if self.user_service.is_expired(verification):
            self.user_repository.delete_two_factor_verification(verification)
            raise DomainException(
                message="La verificación ha expirado. Por favor, inicie el proceso de doble factor de autenticación nuevamente.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        verify_pin = self.user_service.verify_pin(verification, pin)
        
        if not verify_pin:
            attempts = self.user_service.increment_attempts(verification)
            if attempts >= 3:
                block_time = 10
                self.user_service.block_user(user, timedelta(minutes=block_time))
                self.user_repository.delete_two_factor_verification(verification)
                raise UserHasBeenBlockedException(block_time)
            raise DomainException(
                message="PIN de verificación incorrecto.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        self.user_repository.delete_two_factor_verification(verification)

        access_token = create_access_token(data={"sub": user.email})
        return TokenResponse(
            access_token=access_token,
            token_type="bearer"
        )