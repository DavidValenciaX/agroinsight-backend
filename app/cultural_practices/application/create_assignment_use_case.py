from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.domain.schemas import AssignmentCreate
from app.farm.infrastructure.sql_repository import FarmRepository
from app.infrastructure.common.response_models import SuccessResponse
from app.infrastructure.common.role_utils import get_admin_role
from app.plot.infrastructure.sql_repository import PlotRepository
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException, InsufficientPermissionsException
from fastapi import status

from app.user.infrastructure.sql_repository import UserRepository

class CreateAssignmentUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)
        self.user_repository = UserRepository(db)
        self.farm_repository = FarmRepository(db)
        self.plot_repository = PlotRepository(db)

    def create_assignment(self, assignment_data: AssignmentCreate, current_user: UserInDB) -> SuccessResponse:
        
        # obtener el id del lote por medio del id de la tarea
        lote_id = self.cultural_practice_repository.get_lote_id_by_tarea_id(assignment_data.tarea_labor_cultural_id)
        if not lote_id:
            raise DomainException(
                message="No se pudo obtener el id del lote.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # obtener el id de la finca por medio del id del lote
        finca_id = self.plot_repository.get_farm_id_by_plot_id(lote_id)
        if not finca_id:
            raise DomainException(
                message="No se pudo obtener el id de la finca.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        #validar que el usuario sea administrador de la finca
        if not self.farm_repository.user_is_farm_admin(current_user.id, finca_id):
            raise InsufficientPermissionsException()

        # Validar que el usuario, tarea y lote existen
        if not self.user_repository.user_exists(assignment_data.usuario_id):
            raise DomainException(
                message="El usuario especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # validar que el usuario es trabajador de la finca
        if not self.farm_repository.user_is_farm_worker(assignment_data.usuario_id, finca_id):
            raise InsufficientPermissionsException()
            
        # Validar que la tarea existe
        if not self.cultural_practice_repository.task_exists(assignment_data.tarea_labor_cultural_id):
            raise DomainException(
                message="La tarea especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Crear la asignación
        if not self.cultural_practice_repository.create_assignment(assignment_data):
            raise DomainException(
                message="No se pudo crear la asignación.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return SuccessResponse(message="Asignación creada exitosamente")