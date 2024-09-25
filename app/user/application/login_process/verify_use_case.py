from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import status
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.services.pin_service import hash_pin
from app.infrastructure.security.security_utils import create_access_token
from app.infrastructure.common.common_exceptions import DomainException


class VerifyUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def execute(self, email: str, pin: str) -> dict:
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
                    message=f"Tu cuenta ha sido bloqueada debido a múltiples intentos fallidos. Intenta nuevamente en {block_time} minutos.",
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