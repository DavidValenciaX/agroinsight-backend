from typing import List, Optional
from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.user.infrastructure.orm_models import Role
from app.user.infrastructure.sql_repository import UserRepository
from app.farm.domain.schemas import FarmUserAssignmentByEmail
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException, InsufficientPermissionsException, MissingTokenException
from fastapi import status
from app.infrastructure.common.response_models import MultipleResponse

# Constantes para roles
ADMIN_ROLE_NAME = "Administrador de Finca"
WORKER_ROLE_NAME = "Trabajador Agrícola"

# Constantes para estados
ACTIVE_STATE_NAME = "active"
LOCKED_STATE_NAME = "locked"
PENDING_STATE_NAME = "pending"
INACTIVE_STATE_NAME = "inactive"

class AssignUsersToFarmUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.farm_repository = FarmRepository(db)
        self.user_repository = UserRepository(db)
    
    def assign_users_by_emails(self, assignment_data: FarmUserAssignmentByEmail, current_user: UserInDB) -> SuccessResponse:

        if not current_user:
            raise MissingTokenException()
        
        farm = self.farm_repository.get_farm_by_id(assignment_data.farm_id)
        if not farm:
            raise DomainException(
                message="La finca especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if not self.farm_repository.user_is_farm_admin(current_user.id, assignment_data.farm_id):
            raise DomainException(
                message="No tienes permisos para asignar usuarios a esta finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        rol_trabajador_agricola = self.get_worker_role()
            
        messages = []
        
        # Validar que los usuarios no tengan un rol asignado en la finca
        for email in assignment_data.user_emails:
            user = self.user_repository.get_user_by_email(email)
            if not user:
                messages.append(f"El usuario con email {email} no existe.")
                continue
            
            user_name = user.nombre + " " + user.apellido
            
            # Validar que el usuario no tenga un rol asignado en la finca
            existing_assignment = self.farm_repository.get_user_farm(user.id, assignment_data.farm_id)
            if existing_assignment:
                messages.append(f"El usuario {user_name} ya tiene un rol asignado en la finca.")
                continue
            
            self.farm_repository.assign_user_to_farm_with_role(user.id, assignment_data.farm_id,  rol_trabajador_agricola.id)
            messages.append(f"El usuario {user_name} ha sido asignado exitosamente a la finca.")
            

        return MultipleResponse(messages=messages)

    def get_worker_role(self) -> Optional[Role]:
        rol_trabajador_agricola = self.user_repository.get_role_by_name(WORKER_ROLE_NAME) 
        if not rol_trabajador_agricola:
            raise DomainException(
                message="No se pudo asignar el rol de Trabajador Agrícola.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return rol_trabajador_agricola