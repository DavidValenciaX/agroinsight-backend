from typing import List
from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.user.infrastructure.sql_repository import UserRepository
from app.farm.domain.schemas import FarmUserAssignmentByEmail
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException, InsufficientPermissionsException, MissingTokenException
from fastapi import status
from app.infrastructure.common.response_models import MultipleResponse

class AssignUsersToFarmUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.farm_repository = FarmRepository(db)
        self.user_repository = UserRepository(db)
    
    def assign_users_by_emails(self, assignment_data: FarmUserAssignmentByEmail, farm_id: int, current_user: UserInDB) -> SuccessResponse:

        if not current_user:
            raise MissingTokenException()
        
        if farm_id != assignment_data.farm_id:
            raise DomainException(
                message="El ID de la finca en la URL no coincide con el ID de la finca en el cuerpo de la solicitud.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        farm = self.farm_repository.get_farm_by_id(assignment_data.farm_id)
        if not farm:
            raise DomainException(
                message="La finca especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if not self.farm_repository.user_is_farm_admin(current_user.id, assignment_data.farm_id):
            raise InsufficientPermissionsException()
        
        rol_trabajador_agricola = self.user_repository.get_worker_role()
            
        messages = []
        
        # Validar que los usuarios no tengan un rol asignado en la finca
        for email in assignment_data.user_emails:
            user = self.user_repository.get_user_by_email(email)
            if not user:
                messages.append(f"El usuario con email {email} no existe.")
                continue
            
            user_name = user.nombre + " " + user.apellido
            
            # Validar que el usuario no tenga un rol asignado en la finca
            existing_assignment = self.farm_repository.get_user_farm_role(user.id, assignment_data.farm_id)
            if existing_assignment:
                messages.append(f"El usuario {user_name} ya tiene un rol asignado en la finca.")
                continue
            
            self.farm_repository.assign_user_to_farm(assignment_data.farm_id, user.id, rol_trabajador_agricola.id)
            messages.append(f"El usuario {user_name} ha sido asignado exitosamente a la finca.")
            

        return MultipleResponse(messages=messages)
