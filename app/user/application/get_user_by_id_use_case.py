from sqlalchemy.orm import Session
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.schemas import UserResponse
from app.infrastructure.common.common_exceptions import InsufficientPermissionsException, MissingTokenException, UserNotRegisteredException

class GetUserByIdUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def execute(self, user_id: int, current_user):
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
        
        return UserResponse(
            id=user.id,
            nombre=user.nombre,
            apellido=user.apellido,
            email=user.email,
            estado=user.estado.nombre,
            rol=", ".join([role.nombre for role in user.roles]) if user.roles else "Rol no asignado"
        )