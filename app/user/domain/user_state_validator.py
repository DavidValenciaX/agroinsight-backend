from datetime import datetime, timezone
from typing import Optional
from fastapi import status
from app.infrastructure.common.common_exceptions import DomainException, UserStateException
from enum import Enum, auto
from sqlalchemy.orm import Session
from app.infrastructure.common.datetime_utils import ensure_utc, datetime_utc_time
from app.user.services.user_service import UserService
from app.user.domain.schemas import UserInDB
from app.user.infrastructure.sql_repository import UserRepository
from app.user.infrastructure.orm_models import UserState as UserStateModel

# Constantes para roles
ADMIN_ROLE_NAME = "Administrador de Finca"
WORKER_ROLE_NAME = "Trabajador Agrícola"

class UserState(Enum):
    ACTIVE = auto()
    INACTIVE = auto()
    LOCKED = auto()
    PENDING = auto()

class UserStateValidator:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)
        self.user_service = UserService(db)
        
    def validate_user_state(self, user, allowed_states=None, disallowed_states=None):
        self.allowed_states = allowed_states
        self.disallowed_states = disallowed_states
        return self.validate_state(user)

    def validate_state(self, user):
        user_state = self.get_user_state(user)

        if self.allowed_states and user_state not in self.allowed_states:
            return self.handle_disallowed_state(user_state, user)

        if self.disallowed_states and user_state in self.disallowed_states:
            return self.handle_disallowed_state(user_state, user)

        if user_state == UserState.LOCKED:
            return self.handle_locked_state(user)

        return None

    def get_user_state(self, user):
        active_state = self.user_service.get_user_state(self.user_service.ACTIVE_STATE_NAME)
        inactive_state = self.user_service.get_user_state(self.user_service.INACTIVE_STATE_NAME)
        locked_state = self.user_service.get_user_state(self.user_service.LOCKED_STATE_NAME)
        pending_state = self.user_service.get_user_state(self.user_service.PENDING_STATE_NAME)
        if active_state and user.state_id == active_state.id:
            return UserState.ACTIVE
        elif inactive_state and user.state_id == inactive_state.id:
            return UserState.INACTIVE
        elif locked_state and user.state_id == locked_state.id:
            return UserState.LOCKED
        elif pending_state and user.state_id == pending_state.id:
            return UserState.PENDING
        else:
            raise UserStateException(
                message="Estado de usuario no reconocido.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                user_state="unknown"
            )

    def handle_disallowed_state(self, state, user):
        if state == UserState.ACTIVE:
            raise UserStateException(
                message="La cuenta ya está registrada y activa.",
                status_code=status.HTTP_400_BAD_REQUEST,
                user_state="active"
            )
        elif state == UserState.INACTIVE:
            raise UserStateException(
                message="La cuenta fue eliminada del sistema.",
                status_code=status.HTTP_410_GONE,
                user_state="inactive"
            )
        elif state == UserState.PENDING:
            raise UserStateException(
                message="La cuenta está pendiente de confirmación. Por favor, confirma el registro.",
                status_code=status.HTTP_400_BAD_REQUEST,
                user_state="pending"
            )
        elif state == UserState.LOCKED:
            return self.handle_locked_state(user)
        
    def should_unlock_user(self, user: UserInDB) -> bool:
        """Verifica si el usuario cumple las condiciones para ser desbloqueado."""
        current_time = datetime_utc_time()
        return ensure_utc(user.locked_until) and current_time > ensure_utc(user.locked_until)

    def handle_locked_state(self, user: UserInDB):
        # Verifica si el usuario debería desbloquearse
        if self.should_unlock_user(user):
            try:
                # Intenta desbloquear al usuario
                if self.unlock_user(user):
                    # Si el desbloqueo fue exitoso, valida el estado actualizado del usuario
                    return self.validate_state(user)
            except Exception as e:
                raise DomainException(
                    message=f"Error al intentar desbloquear el usuario: {str(e)}",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                ) from e
        
        # Si el usuario no cumple las condiciones para desbloquearse, calcula el tiempo restante y lanza una excepción
        time_left = user.locked_until - datetime_utc_time()
        minutos_restantes = max(time_left.seconds // 60, 1)  # Asegura al menos 1 minuto
        raise UserStateException(
            message=f"La cuenta está bloqueada. Intenta nuevamente en {minutos_restantes} minutos.",
            status_code=status.HTTP_403_FORBIDDEN,
            user_state="locked"
        )
        
    def is_user_unlocked(self, user: UserInDB) -> bool:
        """Verifica si el usuario está desbloqueado revisando que `locked_until` sea None y tenga el estado de 'activo'."""
        return user.locked_until is None and user.state_id == self.user_service.get_user_state(self.user_service.ACTIVE_STATE_NAME).id

    def unlock_user(self, user: UserInDB) -> bool:
        """Desbloquea al usuario."""
        user.failed_attempts = 0
        user.locked_until = None
        user.state_id = self.user_service.get_user_state(self.user_service.ACTIVE_STATE_NAME).id
        
        # Actualiza el usuario en la base de datos
        updated_user = self.user_repository.update_user(user)
        
        # Verifica si el usuario está efectivamente desbloqueado
        if not updated_user or not self.is_user_unlocked(updated_user):
            raise DomainException(
                message="No se pudo desbloquear al usuario.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return True  # Usuario desbloqueado exitosamente