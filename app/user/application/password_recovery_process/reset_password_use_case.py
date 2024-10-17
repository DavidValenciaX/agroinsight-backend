from typing import Optional
from sqlalchemy.orm import Session
from fastapi import status
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.infrastructure.security.security_utils import hash_password, verify_password
from app.user.infrastructure.orm_models import PasswordRecovery
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException

class ResetPasswordUseCase:
    """
    Caso de uso para restablecer la contraseña de un usuario.

    Esta clase maneja el proceso de restablecimiento de contraseña, incluyendo
    la validación del estado del usuario, la verificación del PIN de recuperación,
    y la actualización de la contraseña en la base de datos.

    Attributes:
        db (Session): Sesión de base de datos para operaciones de persistencia.
        user_repository (UserRepository): Repositorio para operaciones relacionadas con usuarios.
        state_validator (UserStateValidator): Validador del estado del usuario.
    """

    def __init__(self, db: Session):
        """
        Inicializa una nueva instancia de ResetPasswordUseCase.

        Args:
            db (Session): Sesión de base de datos para operaciones de persistencia.
        """
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)

    def reset_password(self, email: str, new_password: str) -> SuccessResponse:
        """
        Restablece la contraseña de un usuario.

        Este método valida el estado del usuario, verifica la existencia de una solicitud
        de recuperación de contraseña válida, y actualiza la contraseña del usuario.

        Args:
            email (str): Correo electrónico del usuario.
            new_password (str): Nueva contraseña a establecer.

        Returns:
            SuccessResponse: Respuesta indicando que la contraseña se restableció correctamente.

        Raises:
            UserNotRegisteredException: Si el usuario no está registrado.
            DomainException: Si no hay una solicitud de recuperación válida, el PIN no está confirmado,
                             la nueva contraseña es igual a la anterior, o hay otros errores.
        """
        user = self.user_repository.get_user_with_password_recovery(email)
        if not user:
            raise UserNotRegisteredException()
            
        state_validation_result = self.state_validator.validate_user_state(
            user,
            allowed_states=[UserState.ACTIVE],
            disallowed_states=[UserState.INACTIVE, UserState.PENDING, UserState.LOCKED]
        )
        if state_validation_result:
            return state_validation_result

        recovery = self.get_last_password_recovery(user.recuperacion_contrasena)

        if not recovery:
            raise DomainException(
                message="No hay un registro de recuperación de contraseña pendiente.",
                status_code=status.HTTP_404_NOT_FOUND
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
        if not self.user_repository.update_user(user):
            raise DomainException(
                message="No se pudo actualizar la contraseña del usuario.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        if not self.user_repository.delete_password_recovery(recovery):
            raise DomainException(
                message="No se pudo eliminar el registro de recuperación de contraseña.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return SuccessResponse(
            message= "Contraseña restablecida correctamente."
        )
        
    def get_last_password_recovery(self, recovery: PasswordRecovery) -> Optional[PasswordRecovery]:
        """
        Obtiene la última recuperación de contraseña del usuario.

        Esta función también elimina todas las recuperaciones anteriores a la última.

        Args:
            recovery (PasswordRecovery): Objeto o lista de objetos de recuperación de contraseña.

        Returns:
            Optional[PasswordRecovery]: La última recuperación de contraseña, o None si no hay ninguna.
        """
        if isinstance(recovery, list) and recovery:
            recovery.sort(key=lambda r: r.created_at)
            latest_recovery = recovery[-1]
            for old_recovery in recovery[:-1]:
                self.user_repository.delete_password_recovery(old_recovery)
            return latest_recovery
        return None
