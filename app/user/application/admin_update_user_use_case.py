from sqlalchemy.orm import Session
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.schemas import AdminUserUpdate, UserResponse, UserInDB
from app.infrastructure.common.common_exceptions import DomainException, InsufficientPermissionsException, UserAlreadyRegisteredException, UserNotRegisteredException
from fastapi import status
from app.infrastructure.mappers.response_mappers import map_user_to_response

class AdminUpdateUserUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def execute(self, user_id: int, user_update: AdminUserUpdate, current_user: UserInDB) -> UserResponse:
        # Obtener los roles que tienen permisos administrativos
        admin_roles = self.user_repository.get_admin_roles()
        admin_role_ids = {admin_role.id for admin_role in admin_roles}
        
        # Verificar si el usuario actual tiene uno de los roles administrativos
        if not any(role.id in admin_role_ids for role in current_user.roles):
            raise InsufficientPermissionsException()
        
        # Verificar si el usuario a actualizar existe
        user_to_update = self.user_repository.get_user_by_id(user_id)
        if not user_to_update:
            raise UserNotRegisteredException()
        
        # Verificar si el nuevo email está en uso por otro usuario
        if user_update.email and user_update.email != user_to_update.email:
            existing_user = self.user_repository.get_user_by_email(user_update.email)
            if existing_user:
                raise UserAlreadyRegisteredException()
        
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
        return map_user_to_response(updated_user)