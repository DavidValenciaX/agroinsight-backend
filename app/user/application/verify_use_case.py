from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.user.infrastructure.sql_repository import UserRepository
from app.core.services.pin_service import hash_pin

class VerifyUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def verify_two_factor_auth(self, email: str, pin: str):
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        if user.locked_until:
            user.locked_until = user.locked_until.replace(tzinfo=timezone.utc)

        # Verificar si la cuenta del usuario está bloqueada
        locked_state_id = self.user_repository.get_locked_user_state_id()
        if user.state_id == locked_state_id and user.locked_until > datetime.now(timezone.utc):
            
            time_left = user.locked_until - datetime.now(timezone.utc)
            raise HTTPException(
                status_code=403,
                detail=f"Su cuenta está bloqueada. Intente nuevamente en {time_left.seconds // 60} minutos."
            )

        # Verificar si el PIN es correcto y no ha expirado
        pin_hash = hash_pin(pin)
        verification = self.user_repository.get_two_factor_verification(user.id, pin_hash)

        if not verification:
            self.handle_failed_verification(user.id)
            raise HTTPException(status_code=400, detail="Código de verificación inválido o expirado")

        # Eliminar el registro de verificación si el PIN es correcto
        self.user_repository.delete_two_factor_verification(user.id)

        # Devolver el usuario autenticado
        return user
    
    def handle_failed_verification(self, user_id: int):
        attempts = self.user_repository.increment_two_factor_attempts(user_id)

        if attempts >= 3:
            raise HTTPException(
                status_code=403,
                detail="Su cuenta ha sido bloqueada debido a múltiples intentos fallidos. Intente nuevamente en 10 minutos."
            )