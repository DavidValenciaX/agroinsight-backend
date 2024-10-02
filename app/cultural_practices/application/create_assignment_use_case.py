from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.domain.schemas import AssignmentCreate
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException, InsufficientPermissionsException
from fastapi import status

class CreateAssignmentUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)

    def execute(self, assignment_data: AssignmentCreate, current_user: UserInDB) -> SuccessResponse:
        if not self.user_can_create_assignment(current_user):
            raise InsufficientPermissionsException()

        # Validar que el usuario, tarea y lote existen
        if not self.cultural_practice_repository.user_exists(assignment_data.usuario_id):
            raise DomainException(
                message="El usuario especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if not self.cultural_practice_repository.task_exists(assignment_data.tarea_labor_cultural_id):
            raise DomainException(
                message="La tarea especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Crear la asignación
        assignment = self.cultural_practice_repository.create_assignment(assignment_data)
        if not assignment:
            raise DomainException(
                message="No se pudo crear la asignación.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return SuccessResponse(message="Asignación creada exitosamente")

    def user_can_create_assignment(self, user: UserInDB) -> bool:
        allowed_roles = ["Superusuario", "Administrador de Finca"]
        return any(role.nombre in allowed_roles for role in user.roles)