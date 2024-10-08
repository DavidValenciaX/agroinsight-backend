from sqlalchemy.orm import Session
from fastapi import status
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.infrastructure.security.security_utils import hash_password, verify_password
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException

class ResetPasswordUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(self.user_repository)

    def reset_password(self, email: str, new_password: str) -> SuccessResponse:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise UserNotRegisteredException()
            
        # Validar el estado del usuario
        state_validation_result = self.state_validator.validate_user_state(
            user,
            allowed_states=[UserState.ACTIVE],
            disallowed_states=[UserState.INACTIVE, UserState.PENDING, UserState.LOCKED]
        )
        if state_validation_result:
            return state_validation_result

        recovery = self.user_repository.get_password_recovery(user.id)

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

        return SuccessResponse(
            message= "Contraseña restablecida correctamente."
        )