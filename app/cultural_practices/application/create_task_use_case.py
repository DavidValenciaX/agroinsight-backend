from sqlalchemy.orm import Session
from app.cultural_practices.application.services.task_service import TaskService
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.domain.schemas import TaskCreate, SuccessTaskCreateResponse
from app.farm.application.services.farm_service import FarmService
from app.farm.infrastructure.sql_repository import FarmRepository
from app.plot.infrastructure.sql_repository import PlotRepository
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class CreateTaskUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)
        self.farm_repository = FarmRepository(db)
        self.plot_repository = PlotRepository(db)
        self.farm_service = FarmService(db)
        self.task_service = TaskService(db)
        
    def create_task(self, task_data: TaskCreate, current_user: UserInDB) -> SuccessTaskCreateResponse:
        
        plot = self.plot_repository.get_plot_by_id(task_data.lote_id)
        if not plot:
            raise DomainException(
                message="No se pudo obtener el lote.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # buscar el id de la finca por medio del id del lote
        farm = self.farm_repository.get_farm_by_id(plot.finca_id)
        if not farm:
            raise DomainException(
                message="No se pudo obtener la finca.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        #validar que el usuario sea administrador de la finca
        if not self.farm_service.user_is_farm_admin(current_user.id, farm.id):
            raise DomainException(
                message="No tienes permisos para crear tareas en esta finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar si el tipo de labor cultural existe
        if not self.cultural_practice_repository.get_task_type_by_id(task_data.tipo_labor_id):
            raise DomainException(
                message="El tipo de labor cultural especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Verificar si el estado de tarea existe
        task_state = self.cultural_practice_repository.get_task_state_by_id(task_data.estado_id)
        if not task_state:
            raise DomainException(
                message="El estado de tarea especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Crear la tarea
        task = self.cultural_practice_repository.create_task(task_data)
        if not task:
            raise DomainException(
                message="No se pudo crear la tarea de labor cultural.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return SuccessTaskCreateResponse(message="Tarea creada exitosamente", task_id=task.id)
