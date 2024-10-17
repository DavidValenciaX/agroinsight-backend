from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.farm.infrastructure.sql_repository import FarmRepository
from app.infrastructure.common.response_models import SuccessResponse
from app.plot.infrastructure.sql_repository import PlotRepository
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

PROGRAMADA = 'Programada'
EN_PROGRESO = 'En Progreso'
COMPLETADA = 'Completada'
CANCELADA = 'Cancelada'
PENDIENTE = 'Pendiente'
RETRASADA = 'Retrasada'
FALLIDA = 'Fallida'
REVISADA = 'Revisada'
APROBADA = 'Aprobada'
POSTERGADA = 'Postergada'
FINALIZADA = 'Finalizada'

class ChangeTaskStateUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)
        self.plot_repository = PlotRepository(db)
        self.farm_repository = FarmRepository(db)
        
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

        # Start the task
        if not self.assign_task_state(task_id, state_id):
            raise DomainException(
                message="No se pudo cambiar el estado de la tarea.",
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
        # get plot id by task id
        plot_id = self.cultural_practice_repository.get_plot_id_by_task_id(task_id)
        if not plot_id:
            raise DomainException(
                message="No se pudo obtener el id del lote.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # get farm id by plot id
        farm_id = self.plot_repository.get_farm_id_by_plot_id(plot_id)
        if not farm_id:
            raise DomainException(
                message="No se pudo obtener el id de la finca.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        # verify if user is admin of the farm
        return self.farm_repository.user_is_farm_admin(user_id, farm_id)
    
    def assign_task_state(self, task_id: int, state_id: int) -> bool:
        # get task by id
        task = self.cultural_practice_repository.get_task_by_id(task_id)
        if not task:
            raise DomainException(
                message="No se pudo obtener la tarea.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # update task state
        task.estado_id = state_id
        self.db.commit()
        self.db.refresh(task)
        return True
            
            
            
