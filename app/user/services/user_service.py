from datetime import timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import status
from app.infrastructure.common.datetime_utils import datetime_utc_time, ensure_utc
from app.infrastructure.services.pin_service import generate_pin, hash_pin
from app.infrastructure.services.email_service import send_email
from app.user.infrastructure.orm_models import User, UserConfirmation, TwoStepVerification, PasswordRecovery, UserState
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException, UserStateException

class UserService:
    # Constantes para roles
    ADMIN_ROLE_NAME = "Administrador de Finca"
    WORKER_ROLE_NAME = "Trabajador Agrícola"

    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def generate_pin_and_expiration(self, expiration_minutes: int = 10) -> Tuple[str, str, timedelta]:
        pin, pin_hash = generate_pin()
        expiration_datetime = datetime_utc_time() + timedelta(minutes=expiration_minutes)
        return pin, pin_hash, expiration_datetime

    def send_email_with_pin(self, email: str, pin: str, subject: str, text_content: str, html_content: str) -> bool:
        return send_email(email, subject, text_content, html_content)
    
    def verify_pin(self, entity, pin: str) -> bool:
        pin_hash = hash_pin(pin)
        return entity.pin == pin_hash

    def is_recently_requested(self, entity, minutes: int = 3) -> bool:
        """
        Verifica si una solicitud fue realizada recientemente dentro de un tiempo especificado.

        Args:
            entity: La entidad a verificar, que debe tener un atributo 'created_at'.
            minutes (int): El tiempo en minutos para considerar como reciente. Por defecto es 3 minutos.

        Returns:
            bool: True si la solicitud fue realizada dentro del tiempo especificado, False en caso contrario.
        """
        return (datetime_utc_time() - ensure_utc(entity.created_at)).total_seconds() < minutes * 60

    def delete_entity(self, entity):
        """
        Elimina una entidad específica del repositorio correspondiente.

        Args:
            entity: La entidad a eliminar. Puede ser una instancia de UserConfirmation, TwoStepVerification o PasswordRecovery.

        Raises:
            ValueError: Si la entidad no es de un tipo reconocido.
        """
        if isinstance(entity, UserConfirmation):
            self.user_repository.delete_user_confirmation(entity)
        elif isinstance(entity, TwoStepVerification):
            self.user_repository.delete_two_factor_verification(entity)
        elif isinstance(entity, PasswordRecovery):
            self.user_repository.delete_password_recovery(entity)
        else:
            raise ValueError("Entidad no reconocida para eliminación.")

    def is_expired(self, entity) -> bool:
        """
        Verifica si una entidad ha expirado.

        Args:
            entity: La entidad a verificar, que debe tener un atributo 'expiracion'.

        Returns:
            bool: True si la entidad ha expirado, False en caso contrario.
        """
        return entity.expiracion < datetime_utc_time()

    def block_user(self, user: User, lock_duration: timedelta) -> bool:
        """
        Bloquea al usuario por un período de tiempo específico.

        Args:
            user (User): Usuario a bloquear.
            lock_duration (timedelta): Duración del bloqueo.

        Returns:
            bool: True si el usuario fue bloqueado exitosamente, False en caso contrario.

        Raises:
            DomainException: Si no se pudo bloquear al usuario.
        """
        try:
            user.locked_until = datetime_utc_time() + lock_duration
            user.state_id = self.get_user_state(self.LOCKED_STATE_NAME).id
            if not self.user_repository.update_user(user):
                raise DomainException(
                    message="No se pudo actualizar el estado del usuario.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            if not self.is_user_blocked(user):
                raise DomainException(
                    message="No se pudo bloquear el usuario.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return True
        except Exception as e:
            raise DomainException(
                message=f"Error al bloquear el usuario: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def is_user_blocked(self, user: User) -> bool:
        """
        Verifica si el usuario está bloqueado.

        Args:
            user (User): Objeto de usuario a verificar.

        Returns:
            bool: True si el usuario está bloqueado, False en caso contrario.
        """
        return user.locked_until and datetime_utc_time() < user.locked_until and user.state_id == self.get_user_state(self.LOCKED_STATE_NAME).id

    def increment_attempts(self, entity):
        """
        Incrementa el número de intentos de una entidad y actualiza la base de datos.

        Args:
            entity: La entidad cuyo número de intentos se incrementará. Puede ser una instancia de UserConfirmation, 
                    TwoStepVerification o PasswordRecovery.

        Returns:
            int: El número actualizado de intentos de la entidad.
        """
        entity.intentos += 1
        if isinstance(entity, UserConfirmation):
            self.user_repository.update_user_confirmation(entity)
        elif isinstance(entity, TwoStepVerification):
            self.user_repository.update_two_factor_verification(entity)
        elif isinstance(entity, PasswordRecovery):
            self.user_repository.update_password_recovery(entity)
        return entity.intentos
    
    def get_user_state(self, state_name: str) -> Optional[UserState]:
        """
        Obtiene el estado de usuario correspondiente al nombre proporcionado.

        Args:
            state_name (str): El nombre del estado de usuario a buscar.

        Returns:
            Optional[UserState]: El estado de usuario correspondiente al nombre proporcionado, o None si no se encuentra.

        Raises:
            UserStateException: Si no se puede encontrar el estado de usuario.
        """
        state = self.user_repository.get_state_by_name(state_name)
        if not state:
            raise UserStateException(
                message=f"No se pudo encontrar el estado de usuario {state_name}.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                user_state="unknown"
            )
        return state
    
    def get_last(self, entities):
        """
        Obtiene la última entidad de una lista de entidades y elimina las entidades anteriores.

        Este método ordena las entidades por su fecha de creación, obtiene la última entidad
        y elimina las entidades anteriores de la lista.

        Args:
            entities (list): Lista de entidades a procesar. Cada entidad debe tener un atributo 'created_at'.

        Returns:
            La última entidad de la lista ordenada por fecha de creación, o None si la lista está vacía o no es una lista.
        """
        if isinstance(entities, list) and entities:
            entities.sort(key=lambda e: e.created_at)
            latest_entity = entities[-1]
            for old_entity in entities[:-1]:
                self.delete_entity(old_entity)
            return latest_entity
        return None