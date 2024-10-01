from sqlalchemy.orm import Session
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.schemas import UserUpdate, UserResponse, UserInDB
from app.infrastructure.common.common_exceptions import DomainException, UserAlreadyRegisteredException
from fastapi import status
from app.infrastructure.mappers.response_mappers import map_user_to_response

class UpdateUserInfoUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def execute(self, current_user: UserInDB, user_update: UserUpdate) -> UserResponse:
        # Verificar si el email ya está en uso por otro usuario
        if user_update.email and user_update.email != current_user.email:
            existing_user = self.user_repository.get_user_by_email(user_update.email)
            if existing_user:
                raise UserAlreadyRegisteredException()
        
        # Actualizar la información del usuario
        updated_user = self.user_repository.update_user_info(current_user, user_update.model_dump(exclude_unset=True))
        
        if not updated_user:
            raise DomainException(
                message="No se pudo actualizar la información del usuario.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Usar la función de mapeo para construir UserResponse
        return map_user_to_response(updated_user)
