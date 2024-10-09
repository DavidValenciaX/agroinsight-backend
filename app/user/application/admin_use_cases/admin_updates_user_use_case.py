from sqlalchemy.orm import Session
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.schemas import AdminUserUpdate, UserResponse, UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from app.infrastructure.common.response_models import SuccessResponse
class AdminUpdatesUserUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def admin_updates_user(self, user_id: int, user_update: AdminUserUpdate, current_user: UserInDB) -> UserResponse:
        
        # Verificar si el usuario a actualizar existe
        user_to_update = self.user_repository.get_user_by_id(user_id)
        if not user_to_update:
            raise DomainException(
                message="El usuario con este id no está registrado",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar si el nuevo email está en uso por otro usuario
        if user_update.email and user_update.email != user_to_update.email:
            existing_user = self.user_repository.get_user_by_email(user_update.email)
            if existing_user:
                raise DomainException(
                    message="El email ya está en uso por otro usuario",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        # Actualizar la información del usuario
        updated_user = self.user_repository.update_user_info_by_admin(
            user_to_update, user_update.model_dump(exclude_unset=True)
        )
        
        if not updated_user:
            raise DomainException(
                message="No se pudo actualizar la información del usuario.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Usar la función de mapeo para construir UserResponse
        return SuccessResponse(
            message="Usuario actualizado correctamente"
        )
