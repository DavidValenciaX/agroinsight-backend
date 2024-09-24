from sqlalchemy.orm import Session
from app.user.infrastructure.sql_repository import UserRepository
from app.core.common_exceptions import DomainException
from fastapi import status

class DeactivateUserUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
    
    def execute(self, user_id: int, current_user):
        # Verificar si el usuario actual tiene permisos de administrador
        admin_roles = self.user_repository.get_admin_roles()
        admin_role_ids = {role.id for role in admin_roles}
        
        if not any(role.id in admin_role_ids for role in current_user.roles):
            raise DomainException(
                message="No tienes permisos para desactivar usuarios.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar si el usuario a desactivar existe
        user_to_deactivate = self.user_repository.get_user_by_id(user_id)
        if not user_to_deactivate:
            raise DomainException(
                message="Usuario no encontrado.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar si el usuario ya está desactivado
        inactive_state_id = self.user_repository.get_inactive_user_state_id()
        if user_to_deactivate.state_id == inactive_state_id:
            raise DomainException(
                message="El usuario ya está desactivado.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Desactivar el usuario
        success = self.user_repository.deactivate_user(user_id)
        if not success:
            raise DomainException(
                message="No se pudo desactivar el usuario. Intenta nuevamente.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return {"message": "Usuario desactivado exitosamente."}