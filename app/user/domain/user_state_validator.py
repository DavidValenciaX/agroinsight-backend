from datetime import datetime, timezone
from typing import Optional
from fastapi import status
from app.infrastructure.common.common_exceptions import UserStateException
from enum import Enum, auto
from sqlalchemy.orm import Session
from app.infrastructure.common.datetime_utils import ensure_utc, datetime_utc_time
from app.user.domain.schemas import UserInDB
from app.user.infrastructure.sql_repository import UserRepository
from app.user.infrastructure.orm_models import UserState as UserStateModel

# Constantes para roles
ADMIN_ROLE_NAME = "Administrador de Finca"
WORKER_ROLE_NAME = "Trabajador agrícola"
UNCONFIRMED_ROLE_NAME = "Rol no confirmado"
UNASSIGNED_ROLE_NAME = "Rol no asignado"

# Constantes para estados
ACTIVE_STATE_NAME = "active"
LOCKED_STATE_NAME = "locked"
PENDING_STATE_NAME = "pending"
INACTIVE_STATE_NAME = "inactive"

class UserState(Enum):
    ACTIVE = auto()
    INACTIVE = auto()
    LOCKED = auto()
    PENDING = auto()

class UserStateValidator:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)

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
        active_state = self.get_active_user_state()
        inactive_state = self.get_inactive_user_state()
        locked_state = self.get_locked_user_state()
        pending_state = self.get_pending_user_state()
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

    def handle_locked_state(self, user: UserInDB):
        if not self.try_unlock_user(user):
            # Si el usuario sigue bloqueado, calculamos el tiempo restante y lanzamos una excepción
            time_left = user.locked_until - datetime_utc_time()
            minutos_restantes = max(time_left.seconds // 60, 1)  # Aseguramos que sea al menos 1 minuto
            raise UserStateException(
                message=f"La cuenta está bloqueada. Intenta nuevamente en {minutos_restantes} minutos.",
                status_code=status.HTTP_403_FORBIDDEN,
                user_state="locked"
            )
            
        # Si el usuario se desbloqueó exitosamente, volver a validar el estado
        return self.validate_state(user)


    def try_unlock_user(self, user: UserInDB):
        current_time = datetime_utc_time()
        
        if ensure_utc(user.locked_until) and current_time > ensure_utc(user.locked_until):
            user.failed_attempts = 0
            user.locked_until = None
            user.state_id = self.get_active_user_state().id
            updated_user = self.user_repository.update_user(user)
            
            if updated_user and updated_user.state_id == self.get_active_user_state().id:
                return True  # Usuario desbloqueado exitosamente
        
        return False  # Usuario sigue bloqueado
    
    def get_active_user_state(self) -> Optional[UserStateModel]:
        return self.user_repository.get_state_by_name(ACTIVE_STATE_NAME)
    
    def get_locked_user_state(self) -> Optional[UserStateModel]:
        return self.user_repository.get_state_by_name(LOCKED_STATE_NAME)
    
    def get_pending_user_state(self) -> Optional[UserStateModel]:
        return self.user_repository.get_state_by_name(PENDING_STATE_NAME)
    
    def get_inactive_user_state(self) -> Optional[UserStateModel]:
        return self.user_repository.get_state_by_name(INACTIVE_STATE_NAME)