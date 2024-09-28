from sqlalchemy.orm import Session
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.schemas import UserUpdate, UserResponse, UserInDB
from app.infrastructure.common.common_exceptions import DomainException, UserAlreadyRegisteredException
from fastapi import status

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
        
        # Construir el UserResponse
        return UserResponse(
            id=updated_user.id,
            nombre=updated_user.nombre,
            apellido=updated_user.apellido,
            email=updated_user.email,
            estado=updated_user.estado.nombre,
            rol=", ".join([role.nombre for role in updated_user.roles]) if updated_user.roles else "Rol no asignado"
        )
