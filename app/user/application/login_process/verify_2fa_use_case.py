"""
Módulo para el caso de uso de verificación de autenticación de dos factores.

Este módulo contiene la clase VerifyUseCase que maneja la lógica para verificar
el PIN de autenticación de dos factores proporcionado por el usuario.
"""

from datetime import timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import status
from app.infrastructure.common.datetime_utils import datetime_utc_time
from app.user.domain.schemas import TokenResponse
from app.user.infrastructure.orm_models import TwoStepVerification, User
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.services.pin_service import hash_pin
from app.infrastructure.security.security_utils import create_access_token
from app.infrastructure.common.common_exceptions import DomainException, UserHasBeenBlockedException, UserNotRegisteredException
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.user.infrastructure.orm_models import UserState as UserStateModel

# Constantes para roles
ADMIN_ROLE_NAME = "Administrador de Finca"
WORKER_ROLE_NAME = "Trabajador Agrícola"

# Constantes para estados
ACTIVE_STATE_NAME = "active"
LOCKED_STATE_NAME = "locked"
PENDING_STATE_NAME = "pending"
INACTIVE_STATE_NAME = "inactive"

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
                
        verification = self.get_last_verification(user.verificacion_dos_pasos)
        if not verification:
            raise DomainException(
                message="No hay una verificación de doble factor de autenticación pendiente para reenviar el PIN.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        if self.is_two_factor_verification_expired(verification):
            self.user_repository.delete_two_factor_verification(verification)
            raise DomainException(
                message="La verificación ha expirado. Por favor, inicie el proceso de doble factor de autenticación nuevamente.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        pin_hash = hash_pin(pin)
        verify_pin = verification.pin == pin_hash
        
        if not verify_pin:
            attempts = self.increment_two_factor_attempts(verification)
            if attempts >= 3:
                block_time = 10
                self.block_user(user, timedelta(minutes=block_time))
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
        
    def increment_two_factor_attempts(self, verification: TwoStepVerification) -> int:
        """
        Incrementa el contador de intentos fallidos de verificación de dos factores.

        Args:
            verification (TwoStepVerification): Objeto de verificación de dos factores.

        Returns:
            int: Número actualizado de intentos fallidos.
        """
        verification.intentos += 1
        self.user_repository.update_two_factor_verification(verification)
        return verification.intentos
        
    def is_two_factor_verification_expired(self, verification: TwoStepVerification) -> bool:
        """
        Verifica si la verificación de dos factores ha expirado.

        Args:
            verification (TwoStepVerification): Objeto de verificación de dos factores.

        Returns:
            bool: True si la verificación ha expirado, False en caso contrario.
        """
        return verification.expiracion < datetime_utc_time()
    
    def get_last_verification(self, verification: TwoStepVerification) -> Optional[TwoStepVerification]:
        """
        Obtiene la última verificación de dos factores del usuario.

        Esta función también elimina todas las verificaciones anteriores a la última.

        Args:
            verification (TwoStepVerification): Objeto o lista de objetos de verificación de dos factores.

        Returns:
            Optional[TwoStepVerification]: La última verificación de dos factores, o None si no hay ninguna.
        """
        if isinstance(verification, list) and verification:
            verification.sort(key=lambda v: v.created_at)
            latest_verification = verification[-1]
            for old_verification in verification[:-1]:
                self.user_repository.delete_two_factor_verification(old_verification)
            return latest_verification
        return None
    
    def is_user_blocked(self, user: User) -> bool:
        """
        Verifica si el usuario está bloqueado.

        Args:
            user (User): Objeto de usuario a verificar.

        Returns:
            bool: True si el usuario está bloqueado, False en caso contrario.
        """
        return user.locked_until and datetime_utc_time() < user.locked_until and user.state_id == self.get_locked_user_state().id

    def block_user(self, user: User, lock_duration: timedelta) -> bool:
        """
        Bloquea al usuario por un período de tiempo específico.

        Args:
            user (User): Usuario a bloquear.
            lock_duration (timedelta): Duración del bloqueo.

        Returns:
            bool: True si el usuario fue bloqueado exitosamente, False en caso contrario.

        Raises:
            DomainException: Si no se pudo bloquear al usuario.
        """
        try:
            user.locked_until = datetime_utc_time() + lock_duration
            user.state_id = self.get_locked_user_state().id
            if not self.user_repository.update_user(user):
                raise DomainException(
                    message="No se pudo actualizar el estado del usuario.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
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
        Obtiene el estado de usuario bloqueado.

        Returns:
            Optional[UserStateModel]: El estado de usuario bloqueado, o None si no se encuentra.

        Raises:
            DomainException: Si no se pudo obtener el estado de usuario bloqueado.
        """
        locked_state = self.user_repository.get_state_by_name(LOCKED_STATE_NAME)
        if not locked_state:
            raise DomainException(
                message="No se pudo obtener el estado de usuario bloqueado.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return locked_state
