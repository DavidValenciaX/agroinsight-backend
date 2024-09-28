from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import status
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.services.pin_service import hash_pin
from app.infrastructure.security.security_utils import create_access_token
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException
from app.user.domain.user_state_validator import UserState, UserStateValidator

class VerifyUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(self.user_repository)
        
    def execute(self, email: str, pin: str) -> dict:
        user = self.user_repository.get_user_by_email(email)
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
        pending_verification = self.user_repository.get_user_pending_2fa_verification(user.id)
        if not pending_verification:
            raise DomainException(
                message="No hay una verificación de doble factor de autenticación pendiente para reenviar el PIN.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar si el PIN es correcto y no ha expirado
        pin_hash = hash_pin(pin)
        verify_pin = self.user_repository.get_two_factor_verification(user.id, pin_hash)
        
        if not verify_pin:
            attempts = self.user_repository.increment_two_factor_attempts(user.id)
            if attempts >= 3:
                block_time = 10
                # Bloquear usuario por 10 minutos
                self.user_repository.block_user(user.id, timedelta(minutes=block_time))
                # Eliminar la verificación
                self.user_repository.delete_two_factor_verification(user.id)
                raise DomainException(
                    message=f"La cuenta ha sido bloqueada debido a múltiples intentos fallidos. Intente nuevamente en {block_time} minutos.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )
            raise DomainException(
                message="PIN de verificación inválido o expirado.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Eliminar el registro de verificación si el PIN es correcto
        self.user_repository.delete_two_factor_verification(user.id)

        access_token = create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}
        TokenResponse(
            access_token=access_token,
            token_type="bearer"
        )