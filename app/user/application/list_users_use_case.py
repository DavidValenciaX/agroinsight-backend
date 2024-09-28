from sqlalchemy.orm import Session
from fastapi import status
from app.infrastructure.common.common_exceptions import DomainException, InsufficientPermissionsException
from app.user.domain.schemas import UserResponse
from app.user.infrastructure.sql_repository import UserRepository

class ListUsersUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def execute(self, current_user):
        # Verificar que el usuario actual está autenticado
        if not current_user:
            raise DomainException(
                message="No estás autenticado. Por favor, proporciona un token válido.",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
            
        # Verificar que el usuario actual tiene roles de administrador
        admin_roles = self.user_repository.get_admin_roles()
        if not any(
            role.id in [admin_role.id for admin_role in admin_roles]
            for role in current_user.roles
        ):
            raise InsufficientPermissionsException()
        
        users = self.user_repository.get_all_users()
        if not users:
            return []  # Retornar lista vacía
        
        # Mapeamos los usuarios a UserResponse para devolver la información formateada
        return [
            UserResponse(
                id=user.id,
                nombre=user.nombre,
                apellido=user.apellido,
                email=user.email,
                estado=user.estado.nombre,  # Nombre del estado
                rol=", ".join([role.nombre for role in user.roles]) if user.roles else "Rol no asignado"
            ) for user in users
        ]
