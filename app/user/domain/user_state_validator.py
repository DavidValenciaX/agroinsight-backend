from datetime import datetime, timezone
from fastapi import status
from app.infrastructure.common.common_exceptions import DomainException
from enum import Enum, auto

class UserState(Enum):
    ACTIVE = auto()
    INACTIVE = auto()
    LOCKED = auto()
    PENDING = auto()

class UserStateValidator:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def validate_user_state(self, user, allowed_states=None, disallowed_states=None):
        self.allowed_states = allowed_states
        self.disallowed_states = disallowed_states
        return self._validate_state(user)

    def _validate_state(self, user):
        user_state = self._get_user_state(user)

        if self.allowed_states and user_state not in self.allowed_states:
            return self._handle_disallowed_state(user_state, user)

        if self.disallowed_states and user_state in self.disallowed_states:
            return self._handle_disallowed_state(user_state, user)

        if user_state == UserState.LOCKED:
            return self._handle_locked_state(user)

        return None

    def _get_user_state(self, user):
        if user.state_id == self.user_repository.get_active_user_state_id():
            return UserState.ACTIVE
        elif user.state_id == self.user_repository.get_inactive_user_state_id():
            return UserState.INACTIVE
        elif user.state_id == self.user_repository.get_locked_user_state_id():
            return UserState.LOCKED
        elif user.state_id == self.user_repository.get_pending_user_state_id():
            return UserState.PENDING

    def _handle_disallowed_state(self, state, user):
        if state == UserState.ACTIVE:
            raise DomainException(
                message="La cuenta ya está registrada y activa.",
                status_code=status.HTTP_400_BAD_REQUEST,
                user_state="active"
            )
        elif state == UserState.INACTIVE:
            raise DomainException(
                message="La cuenta fue eliminada del sistema.",
                status_code=status.HTTP_410_GONE,
                user_state="inactive"
            )
        elif state == UserState.PENDING:
            raise DomainException(
            message="La cuenta está pendiente de confirmación. Por favor, confirma el registro.",
            status_code=status.HTTP_400_BAD_REQUEST,
            user_state="pending"
        )
        elif state == UserState.LOCKED:
            return self._handle_locked_state(user)

    def _handle_locked_state(self, user):
        if self._try_unlock_user(user):
            # Si el usuario se desbloqueó exitosamente, volver a validar el estado
            return self._validate_state(user)
        else:
            # Si el usuario sigue bloqueado, calculamos el tiempo restante y lanzamos una excepción
            time_left = user.locked_until - datetime.now(timezone.utc)
            minutos_restantes = max(time_left.seconds // 60, 1)  # Aseguramos que sea al menos 1 minuto
            raise DomainException(
                message=f"La cuenta está bloqueada. Intenta nuevamente en {minutos_restantes} minutos.",
                status_code=status.HTTP_403_FORBIDDEN,
                user_state="locked"
            )

    def _try_unlock_user(self, user):
        current_time = datetime.now(timezone.utc)
        
        if user.locked_until:
            user.locked_until = user.locked_until.replace(tzinfo=timezone.utc)
        
        if user.locked_until and current_time > user.locked_until:
            user.failed_attempts = 0
            user.locked_until = None
            user.state_id = self.user_repository.get_active_user_state_id()
            updated_user = self.user_repository.update_user(user)
            
            if updated_user and updated_user.state_id == self.user_repository.get_active_user_state_id():
                return True  # Usuario desbloqueado exitosamente
        
        return False  # Usuario sigue bloqueado