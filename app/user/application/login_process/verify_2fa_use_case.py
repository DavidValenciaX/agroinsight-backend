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
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)
        
    def verify_2fa(self, email: str, pin: str) -> TokenResponse:
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
                
        # Verificar si hay una confirmación pendiente
        verification = self.get_last_verification(user.verificacion_dos_pasos)
        if not verification:
            raise DomainException(
                message="No hay una verificación de doble factor de autenticación pendiente para reenviar el PIN.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Verificar si la verificación está expirada
        if self.is_two_factor_verification_expired(verification):
            # Eliminar la verificación
            self.user_repository.delete_two_factor_verification(verification)
            raise DomainException(
                message="La verificación ha expirado. Por favor, inicie el proceso de doble factor de autenticación nuevamente.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar si el PIN es correcto
        pin_hash = hash_pin(pin)
        verify_pin = verification.pin == pin_hash
        
        if not verify_pin:
            attempts = self.increment_two_factor_attempts(verification)
            if attempts >= 3:
                block_time = 10
                # Bloquear usuario por 10 minutos
                self.block_user(user, timedelta(minutes=block_time))
                # Eliminar la verificación
                self.user_repository.delete_two_factor_verification(verification)
                raise UserHasBeenBlockedException(block_time)
            raise DomainException(
                message="PIN de verificación incorrecto.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Eliminar el registro de verificación si el PIN es correcto
        self.user_repository.delete_two_factor_verification(verification)

        access_token = create_access_token(data={"sub": user.email})
        return TokenResponse(
            access_token=access_token,
            token_type="bearer"
        )
        
    def increment_two_factor_attempts(self, verification: TwoStepVerification) -> int:
        verification.intentos += 1
        self.user_repository.update_two_factor_verification(verification)
        return verification.intentos
        
    def is_two_factor_verification_expired(self, verification: TwoStepVerification) -> bool:
        """Verifica si la verificación de dos pasos ha expirado."""
        return verification.expiracion < datetime_utc_time()
    
    def get_last_verification(self, verification: TwoStepVerification) -> Optional[TwoStepVerification]:
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
    
    def block_user(self, user: User, lock_duration: timedelta) -> bool:
        user.locked_until = datetime_utc_time() + lock_duration
        user.state_id = self.get_locked_user_state().id
        return self.user_repository.update_user(user)
    
    def get_locked_user_state(self) -> Optional[UserStateModel]:
        return self.user_repository.get_state_by_name(LOCKED_STATE_NAME)