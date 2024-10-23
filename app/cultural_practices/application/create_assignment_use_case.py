from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.domain.schemas import AssignmentCreate, AssignmentCreateSingle
from app.farm.application.services.farm_service import FarmService
from app.infrastructure.common.response_models import MultipleResponse
from app.plot.infrastructure.sql_repository import PlotRepository
from app.farm.infrastructure.sql_repository import FarmRepository
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

from app.user.infrastructure.sql_repository import UserRepository

class CreateAssignmentUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)
        self.user_repository = UserRepository(db)
        self.plot_repository = PlotRepository(db)
        self.farm_repository = FarmRepository(db)
        self.farm_service = FarmService(db)

    def create_assignment(self, assignment_data: AssignmentCreate, current_user: UserInDB) -> MultipleResponse:
        
        # Validar que la tarea existe
        task = self.cultural_practice_repository.get_task_by_id(assignment_data.tarea_labor_cultural_id)
        if not task:
            raise DomainException(
                message="No se pudo obtener la tarea.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # get plot by id
        plot = self.plot_repository.get_plot_by_id(task.lote_id)
        if not plot:
            raise DomainException(
                message="No se pudo obtener el lote.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # get farm by id
        farm = self.farm_repository.get_farm_by_id(plot.finca_id)
        if not farm:
            raise DomainException(
                message="No se pudo obtener la finca.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # validar que el usuario sea administrador de la finca
        if not self.farm_service.user_is_farm_admin(current_user.id, farm.id):
            raise DomainException(
                message="No tienes permisos para asignar tareas en esta finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        messages = []
        success_count = 0
        failure_count = 0

        # Iterar sobre cada usuario_id en usuario_ids
        for usuario_id in assignment_data.usuario_ids:
            # obtener el nombre del usuario
            user = self.user_repository.get_user_by_id(usuario_id)
            if not user:
                messages.append(f"El usuario con ID {usuario_id} especificado no existe.")
                failure_count += 1
                continue
            
            user_name = user.nombre + " " + user.apellido
            
            if current_user.id == usuario_id:
                messages.append(f"El usuario {user_name} es el administrador de la finca.")
                failure_count += 1
                continue
            
            # validar que el usuario es trabajador de la finca
            if not self.farm_service.user_is_farm_worker(usuario_id, farm.id):
                messages.append(f"El usuario {user_name} no es trabajador de la finca.")
                failure_count += 1
                continue
            
            # validar que el usuario no tenga ya asignada esa tarea
            if self.cultural_practice_repository.get_user_task_assignment(usuario_id, assignment_data.tarea_labor_cultural_id):
                messages.append(f"El usuario {user_name} ya tiene asignada la tarea con ID {assignment_data.tarea_labor_cultural_id}.")
                failure_count += 1
                continue
            
            assignment_data_single = AssignmentCreateSingle(
                usuario_id=usuario_id,
                tarea_labor_cultural_id=assignment_data.tarea_labor_cultural_id
            )
            
            if not self.cultural_practice_repository.create_assignment(assignment_data_single):
                messages.append(f"No se pudo crear la asignación para el usuario {user_name}.")
                failure_count += 1
                continue
                
            messages.append(f"Asignación creada exitosamente para el usuario {user_name}.")
            success_count += 1

        if success_count > 0 and failure_count > 0:
            status_code = status.HTTP_207_MULTI_STATUS
        elif success_count == 0:
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_200_OK

        return MultipleResponse(messages=messages, status_code=status_code)
