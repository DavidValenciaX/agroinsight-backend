from typing import List
from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.user.infrastructure.sql_repository import UserRepository
from app.farm.domain.schemas import FarmUserAssignmentByEmail
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException, InsufficientPermissionsException
from fastapi import status

class AssignUsersToFarmUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.farm_repository = FarmRepository(db)
        self.user_repository = UserRepository(db)
    
    def assign_users_by_emails(self, assignment_data: FarmUserAssignmentByEmail, current_user: UserInDB) -> SuccessResponse:

        farm = self.farm_repository.get_farm_by_id(assignment_data.farm_id)
        if not farm:
            raise DomainException(
                message="La finca especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        user_ids = []
        for email in assignment_data.user_emails:
            user = self.user_repository.get_user_by_email(email)
            if not user:
                raise DomainException(
                    message=f"El usuario con email {email} no existe.",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            user_ids.append(user.id)
            
        # Verificar si el usuario tiene el rol de "Administrador de Finca" en la finca
        rol_administrador_finca = self.user_repository.get_role_by_name("Administrador de Finca")
        
        if not rol_administrador_finca:
            raise DomainException(
                message="El rol de 'Administrador de Finca' no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if not self.farm_repository.user_is_farm_admin(current_user.id, assignment_data.farm_id, rol_administrador_finca.id):
            raise InsufficientPermissionsException()
        
        # Buscar el rol de "Trabajador Agrícola"
        rol_trabajador_agricola = self.user_repository.get_role_by_name("Trabajador Agrícola")
        if not rol_trabajador_agricola:
            raise DomainException(
                message="El rol de 'Trabajador Agrícola' no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Validar que los usuarios no tengan un rol asignado en la finca
        for email in assignment_data.user_emails:
            user = self.user_repository.get_user_by_email(email)
            if not user:
                raise DomainException(
                    message=f"El usuario con email {email} no existe.",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            existing_assignment = self.farm_repository.get_user_farm_role(user.id, assignment_data.farm_id)
            if existing_assignment:
                raise DomainException(
                    message=f"El usuario con email {email} ya tiene un rol asignado en la finca.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        self.farm_repository.assign_users_to_farm(assignment_data.farm_id, user_ids, rol_trabajador_agricola.id)

        return SuccessResponse(
            message="Usuarios asignados exitosamente a la finca."
        )