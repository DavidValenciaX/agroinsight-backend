from typing import List, Optional
from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.user.infrastructure.orm_models import Role
from app.user.infrastructure.sql_repository import UserRepository
from app.farm.domain.schemas import FarmUserAssignmentByEmail
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from app.infrastructure.common.response_models import MultipleResponse
from app.user.application.services.user_service import UserService
from app.farm.application.services.farm_service import FarmService

class AssignUsersToFarmUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.farm_repository = FarmRepository(db)
        self.user_repository = UserRepository(db)
        self.farm_service = FarmService(db)
        self.user_service = UserService(db)
    
    def assign_users_by_emails(self, assignment_data: FarmUserAssignmentByEmail, current_user: UserInDB) -> MultipleResponse:
        
        farm = self.farm_repository.get_farm_by_id(assignment_data.farm_id)
        if not farm:
            raise DomainException(
                message="La finca especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if not self.farm_service.user_is_farm_admin(current_user.id, farm.id):
            raise DomainException(
                message="No tienes permisos para asignar usuarios a esta finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        worker_role = self.farm_service.get_worker_role()
            
        messages = []
        success_count = 0
        failure_count = 0
        
        # Validar que los usuarios no tengan un rol asignado en la finca
        for email in assignment_data.user_emails:
            user = self.user_repository.get_user_by_email(email)
            if not user:
                messages.append(f"El usuario con email {email} no existe.")
                failure_count += 1
                continue
            
            user_name = user.nombre + " " + user.apellido
            
            # Validar que el usuario no tenga un rol asignado en la finca
            existing_assignment = self.farm_repository.get_user_farm(user.id, assignment_data.farm_id)
            if existing_assignment:
                messages.append(f"El usuario {user_name} ya tiene un rol asignado en la finca.")
                failure_count += 1
                continue
            
            self.farm_repository.add_user_to_farm_with_role(user.id, assignment_data.farm_id, worker_role.id)
            messages.append(f"El usuario {user_name} ha sido asignado exitosamente a la finca.")
            success_count += 1

        if success_count > 0 and failure_count > 0:
            status_code = status.HTTP_207_MULTI_STATUS
        elif success_count == 0:
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_200_OK

        return MultipleResponse(messages=messages, status_code=status_code)
