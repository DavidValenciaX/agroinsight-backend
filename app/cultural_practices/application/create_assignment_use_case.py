from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.domain.schemas import AssignmentCreate, AssignmentCreateSingle
from app.farm.infrastructure.sql_repository import FarmRepository
from app.infrastructure.common.response_models import MultipleResponse, SuccessResponse
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

    def create_assignment(self, assignment_data: AssignmentCreate, current_user: UserInDB) -> MultipleResponse:
        
        # Validar que la tarea existe
        if not self.cultural_practice_repository.get_task_by_id(assignment_data.tarea_labor_cultural_id):
            raise DomainException(
                message="La tarea especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # obtener el id del lote por medio del id de la tarea
        lote_id = self.cultural_practice_repository.get_plot_id_by_task_id(assignment_data.tarea_labor_cultural_id)
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
            
            # validar que el usuario es trabajador de la finca
            if not self.farm_repository.user_is_farm_worker(usuario_id, finca_id):
                messages.append(f"El usuario {user_name} no es trabajador de la finca.")
                failure_count += 1
                continue
            
            # validar que el usuario no tenga ya asignada esa tarea
            if self.cultural_practice_repository.user_has_assignment(usuario_id, assignment_data.tarea_labor_cultural_id):
                messages.append(f"El usuario {user_name} ya tiene asignada la tarea con ID {assignment_data.tarea_labor_cultural_id}.")
                failure_count += 1
                continue
            
            # Crear la asignación
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
