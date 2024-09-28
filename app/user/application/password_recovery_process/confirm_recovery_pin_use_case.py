
from sqlalchemy.orm import Session
from fastapi import status
from datetime import datetime, timedelta, timezone
from app.infrastructure.services.pin_service import hash_pin
from app.user.domain.schemas import SuccessResponse
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException, UserHasBeenBlockedException, UserNotRegisteredException

class ConfirmRecoveryPinUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(self.user_repository)

    def execute(self, email: str, pin: str) -> SuccessResponse:
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

        recovery = self.user_repository.get_password_recovery(user.id)
        if not recovery:
            raise DomainException(
                message="No hay un registro de recuperación de contraseña pendiente.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Verificar si el PIN proporcionado coincide
        pin_hash = hash_pin(pin)
        if pin_hash != recovery.pin:
            # PIN incorrecto, incrementar los intentos
            recovery.intentos += 1
            if recovery.intentos >= 3:
                block_time = 10
                self.user_repository.delete_password_recovery(user.id)
                locked = self.user_repository.block_user(user.id, timedelta(minutes=block_time))
                if not locked:
                    raise DomainException(
                        message="Error al bloquear al usuario.",
                        status_code=status.HTTP_403_FORBIDDEN
                    )

                raise UserHasBeenBlockedException(block_time)

            else:
                self.user_repository.update_password_recovery(recovery)
                
            raise DomainException(
                message="PIN de verificación inválido o expirado.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        # Marcar el PIN como confirmado
        recovery.pin_confirmado = True
        self.user_repository.update_password_recovery(recovery)
        return SuccessResponse(
                message="PIN de recuperación confirmado correctamente."
            ) 
