from sqlalchemy.orm import Session
from app.user.domain.schemas import UserResponse
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import InsufficientPermissionsException, MissingTokenException, UserNotRegisteredException
from app.infrastructure.mappers.response_mappers import map_user_to_response

class GetUserByIdUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def execute(self, user_id: int, current_user) -> UserResponse:
        if not current_user:
            raise MissingTokenException()
            
        # Verificar que el usuario actual tiene roles de administrador
        admin_roles = self.user_repository.get_admin_roles()
        if not any(
            role.id in [admin_role.id for admin_role in admin_roles]
            for role in current_user.roles
        ):
            raise InsufficientPermissionsException()
        
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            raise UserNotRegisteredException()
        
        # Usar la función de mapeo para construir UserResponse
        return map_user_to_response(user)