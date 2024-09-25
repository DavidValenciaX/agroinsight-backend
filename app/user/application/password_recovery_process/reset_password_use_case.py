from sqlalchemy.orm import Session
from fastapi import status
from datetime import datetime, timezone
from app.infrastructure.security.security_utils import hash_password, verify_password
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException

class ResetPasswordUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def execute(self, email: str, new_password: str) -> dict:
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
                message=f"Tu cuenta está bloqueada. Intenta nuevamente en {minutos_restantes} minutos.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        recovery = self.user_repository.get_password_recovery(user.id)

        if not recovery:
            raise DomainException(
                message="No hay un registro de recuperación de contraseña pendiente.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        if not recovery.pin_confirmado:
            raise DomainException(
                message="El PIN de recuperación no ha sido confirmado.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if verify_password(new_password, user.password):
            raise DomainException(
                message="Asegúrate de que la nueva contraseña sea diferente de la anterior",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        user.password = hash_password(new_password)
        # Actualizar usuario en la base de datos
        updated_user = self.user_repository.update_user(user)
        if not updated_user:
            raise DomainException(
                message="No se pudo actualizar la contraseña del usuario.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Eliminar la solicitud de recuperación de contraseña
        if not self.user_repository.delete_recovery(recovery):
            raise DomainException(
                message="No se pudo eliminar el registro de recuperación de contraseña.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return {"message": "Contraseña restablecida correctamente."}