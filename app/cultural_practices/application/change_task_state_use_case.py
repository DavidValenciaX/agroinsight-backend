from sqlalchemy.orm import Session
from app.cultural_practices.application.services.task_service import TaskService
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.farm.application.services.farm_service import FarmService
from app.infrastructure.common.response_models import SuccessResponse
from app.plot.infrastructure.sql_repository import PlotRepository
from app.farm.infrastructure.sql_repository import FarmRepository
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class ChangeTaskStateUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)
        self.plot_repository = PlotRepository(db)
        self.farm_repository = FarmRepository(db)
        self.farm_service = FarmService(db)
        self.task_service = TaskService(db)
        
    def change_task_state(self, task_id: int, state_id: int, current_user: UserInDB) -> SuccessResponse:
        # Validate task existence
        if not self.cultural_practice_repository.get_task_by_id(task_id):
            raise DomainException(
                message="La tarea especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Validate user permissions
        if not self.user_can_change_task_state(current_user.id, task_id):
            raise DomainException(
                message="No tienes permisos para cambiar el estado de esta tarea.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # get task by id
        task = self.cultural_practice_repository.get_task_by_id(task_id)
        if not task:
            raise DomainException(
                message="No se pudo obtener la tarea.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        target_state = self.cultural_practice_repository.get_task_state_by_id(state_id)
        if not target_state:
            raise DomainException(
                message="No se pudo obtener el estado al cuál se quiere cambiar la tarea.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        task.estado_id = state_id
        if not self.cultural_practice_repository.update_task(task):
            raise DomainException(
                message="No se pudo actualizar el estado de la tarea.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        # get state name by id
        state = self.cultural_practice_repository.get_task_state_by_id(state_id)
        if not state:
            raise DomainException(
                message="No se pudo obtener el estado de la tarea.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return SuccessResponse(
            message="Estado de la tarea cambiado exitosamente a " + state.nombre
        )
    
    def user_can_change_task_state(self, user_id: int, task_id: int) -> bool:
        
        # get task by id
        task = self.cultural_practice_repository.get_task_by_id(task_id)
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
            
        # verify if user is admin of the farm
        return self.farm_service.user_is_farm_admin(user_id, farm.id)
            
            
            
