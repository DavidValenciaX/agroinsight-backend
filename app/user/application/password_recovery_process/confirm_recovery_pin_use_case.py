
from sqlalchemy.orm import Session
from fastapi import status
from datetime import datetime, timedelta, timezone
from app.infrastructure.services.pin_service import hash_pin
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException

class ConfirmRecoveryPinUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def execute(self, email: str, pin: str) -> dict:
        """Confirma el PIN de recuperación de contraseña."""
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise DomainException(
                message="Usuario no encontrado.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Verificar si la cuenta del usuario está pendiente de confirmación
        pending_state_id = self.user_repository.get_pending_user_state_id()
        if user.state_id == pending_state_id:
            raise DomainException(
                message="Tu cuenta está pendiente de confirmación. Por favor, confirma tu registro.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
                
        # Verificar si el usuario ha sido eliminado
        inactive_state_id = self.user_repository.get_inactive_user_state_id()
        if user.state_id == inactive_state_id:
            raise DomainException(
                message="El usuario fue eliminado del sistema.",
                status_code=status.HTTP_410_GONE
            )
        
        # Verificar si la cuenta del usuario está bloqueada
        if user.locked_until:
            user.locked_until = user.locked_until.replace(tzinfo=timezone.utc)

        locked_state_id = self.user_repository.get_locked_user_state_id()
        if user.state_id == locked_state_id and user.locked_until > datetime.now(timezone.utc):
            time_left = user.locked_until - datetime.now(timezone.utc)
            minutos_restantes = time_left.seconds // 60
            raise DomainException(
                message=f"Tu cuenta está bloqueada. Intenta nuevamente en {minutos_restantes} minutos.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        recovery = self.user_repository.get_password_recovery(user.id)
        if not recovery:
            raise DomainException(
                message="No hay un registro de recuperación de contraseña pendiente.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Verificar si el PIN proporcionado coincide
        pin_hash = hash_pin(pin)
        if pin_hash == recovery.pin:
            # Marcar el PIN como confirmado
            recovery.pin_confirmado = True
            self.user_repository.update_password_recovery(recovery)
            return {"message": "PIN de recuperación confirmado correctamente."}
        else:
            # PIN incorrecto, incrementar los intentos
            recovery.intentos += 1
            if recovery.intentos >= 3:
                block_time = 10
                self.user_repository.delete_password_recovery(user.id)
                locked = self.user_repository.block_user(user.id, timedelta(minutes=block_time))
                if locked:
                    raise DomainException(
                        message=f"Tu cuenta ha sido bloqueada debido a múltiples intentos fallidos. Intenta nuevamente en {block_time} minutos.",
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS
                    )
                else:
                    raise DomainException(
                        message="Error al bloquear al usuario.",
                        status_code=status.HTTP_403_FORBIDDEN)
            else:
                self.user_repository.update_password_recovery(recovery)
            raise DomainException(
                message="PIN de verificación inválido o expirado.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
