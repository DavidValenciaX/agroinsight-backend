from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.domain.schemas import AssignmentCreate, AssignmentCreateSingle
from app.farm.infrastructure.sql_repository import FarmRepository
from app.infrastructure.common.response_models import MultipleResponse, SuccessResponse
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
        
        # validar que el usuario sea administrador de la finca
        if not self.farm_repository.user_is_farm_admin(current_user.id, finca_id):
            raise InsufficientPermissionsException()
        
        
        # Validar que la tarea existe
        if not self.cultural_practice_repository.task_exists(assignment_data.tarea_labor_cultural_id):
            raise DomainException(
                message="La tarea especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        messages = []

        # Iterar sobre cada usuario_id en usuario_ids
        for usuario_id in assignment_data.usuario_ids:
            # Validar que el usuario existe
            if not self.user_repository.user_exists(usuario_id):
                messages.append(f"El usuario con ID {usuario_id} especificado no existe.")
                continue
            
            # validar que el usuario es trabajador de la finca
            if not self.farm_repository.user_is_farm_worker(usuario_id, finca_id):
                messages.append(f"El usuario con ID {usuario_id} no es trabajador de la finca.")
                continue
            
            # validar que el usuario no tenga ya asignada esa tarea
            if self.cultural_practice_repository.user_has_assignment(usuario_id, assignment_data.tarea_labor_cultural_id):
                messages.append(f"El usuario con ID {usuario_id} ya tiene asignada la tarea con ID {assignment_data.tarea_labor_cultural_id}.")
                continue
            
            # Crear la asignación
            assignment_data_single = AssignmentCreateSingle(
                usuario_id=usuario_id,
                tarea_labor_cultural_id=assignment_data.tarea_labor_cultural_id,
                notas=assignment_data.notas
            )
            if not self.cultural_practice_repository.create_assignment(assignment_data_single):
                messages.append(f"No se pudo crear la asignación para el usuario con ID {usuario_id}.")
                
            messages.append(f"Asignación creada exitosamente para el usuario con ID {usuario_id}.")
        
        return MultipleResponse(messages=messages)