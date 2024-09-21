from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.user.infrastructure.sql_repository import UserRepository
from app.core.services.pin_service import hash_pin
from app.core.security.security_utils import create_access_token
from app.user.domain.exceptions import DomainException

class VerifyUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def execute(self, email: str, pin: str):
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise DomainException(
                message="Usuario no encontrado",
                status_code=404
            )
            
        # Verificar si la cuenta del usuario está pendiente de confirmación
        pending_state_id = self.user_repository.get_pending_user_state_id()
        if user.state_id == pending_state_id:
            raise DomainException(message="La cuenta del usuario está pendiente de confirmación.", status_code=400)
            
        # Verificar si el usuario ha sido eliminado
        inactive_state_id = self.user_repository.get_inactive_user_state_id()
        if user.state_id == inactive_state_id:
            raise DomainException(message="El usuario fue eliminado del sistema.", status_code=400)
        
        # Verificar si la cuenta del usuario está bloqueada
        if user.locked_until:
            user.locked_until = user.locked_until.replace(tzinfo=timezone.utc)

        locked_state_id = self.user_repository.get_locked_user_state_id()
        if user.state_id == locked_state_id and user.locked_until > datetime.now(timezone.utc):
            time_left = user.locked_until - datetime.now(timezone.utc)
            raise DomainException(
                message=f"Su cuenta está bloqueada. Intente nuevamente en {time_left.seconds // 60} minutos.",
                status_code=403
            )
            
        # Verificar si hay una confirmación pendiente
        pending_verification = self.user_repository.get_user_pending_2fa_verification(user.id)
        if not pending_verification:
            raise DomainException(message="No hay una verificación de doble factor de autenticación pendiente para reenviar el PIN.", status_code=400)
        
        # Verificar si el PIN es correcto y no ha expirado
        pin_hash = hash_pin(pin)
        verify_pin = self.user_repository.get_two_factor_verification(user.id, pin_hash)
        
        if not verify_pin:
            attempts = self.user_repository.increment_two_factor_attempts(user.id)
            if attempts >= 3:
                accessTokenExpireMinutes = 10
                # bloquear usuario por 10 minutos
                self.user_repository.block_user(user.id, timedelta(minutes=accessTokenExpireMinutes))
                # Eliminar la verificación
                self.user_repository.delete_two_factor_verification(user.id)
                raise DomainException(
                    message="Su cuenta ha sido bloqueada debido a múltiples intentos fallidos. Intente nuevamente en 10 minutos.",
                    status_code=403
                )
            raise DomainException(
                message="PIN de verificación inválido o expirado",
                status_code=400
            )

        # Eliminar el registro de verificación si el PIN es correcto
        self.user_repository.delete_two_factor_verification(user.id)

        access_token = create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}