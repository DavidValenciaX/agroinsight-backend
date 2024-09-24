
from sqlalchemy.orm import Session
from fastapi import status
from datetime import datetime, timedelta, timezone
from app.core.services.pin_service import hash_pin
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.exceptions import DomainException

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
                message="La cuenta del usuario está pendiente de confirmación.",
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
                message=f"Su cuenta está bloqueada. Intente nuevamente en {minutos_restantes} minutos.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        recovery = self.user_repository.get_password_recovery(user.id)
        if not recovery:
            raise DomainException(
                message="No hay un registro de recuperación de contraseña pendiente.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Verificar si el PIN proporcionado coincide
        pin_hash = hash_pin(pin)
        if pin_hash == recovery.pin:
            #no se debe eliminar el registro de confirmación sino guardar un campo que diga si es confirmed
            return {"message": "Código de recuperación confirmado correctamente."}
        else:
            # PIN incorrecto, incrementar los intentos
            recovery.intentos += 1
            if recovery.intentos >= 3:
                self.user_repository.delete_password_recovery(user.id)
                locked = self.user_repository.block_user(user.id, timedelta(minutes=10))
                if locked:
                    raise DomainException(
                        message="Su cuenta ha sido bloqueada debido a múltiples intentos fallidos. Intente nuevamente en 10 minutos.",
                        status_code=status.HTTP_403_FORBIDDEN
                    )
                else:
                    raise DomainException(
                        message="No se pudo bloquear al usuario debido a un error interno.",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                self.user_repository.update_password_recovery(recovery)
            raise DomainException(
                message="PIN de verificación inválido o expirado.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
