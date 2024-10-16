from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.domain.schemas import TaskCreate, SuccessTaskCreateResponse
from app.farm.infrastructure.sql_repository import FarmRepository
from app.infrastructure.common.datetime_utils import get_current_date
from app.plot.infrastructure.sql_repository import PlotRepository
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class CreateTaskUseCase:
    COMPLETED_STATE_NAME = "Completada"
    def __init__(self, db: Session):
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)
        self.farm_repository = FarmRepository(db)
        self.plot_repository = PlotRepository(db)

    def create_task(self, tarea_data: TaskCreate, current_user: UserInDB) -> SuccessTaskCreateResponse:
        
        # buscar el id de la finca por medio del id del lote
        finca_id = self.plot_repository.get_farm_id_by_plot_id(tarea_data.lote_id)
        if not finca_id:
            raise DomainException(
                message="No se pudo obtener el id de la finca.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        #validar que el usuario sea administrador de la finca
        if not self.farm_repository.user_is_farm_admin(current_user.id, finca_id):
            raise DomainException(
                message="No tienes permisos para crear tareas en esta finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Validar los datos de entrada
        self.validate_tarea_data(tarea_data)
        
        #validar que el lote existe
        if not self.plot_repository.get_plot_by_id(tarea_data.lote_id):
            raise DomainException(
                message="El lote especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar si el tipo de labor cultural existe
        if not self.cultural_practice_repository.get_task_type_by_id(tarea_data.tipo_labor_id):
            raise DomainException(
                message="El tipo de labor cultural especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Verificar si el estado de tarea existe
        if not self.cultural_practice_repository.get_task_state_by_id(tarea_data.estado_id):
            raise DomainException(
                message="El estado de tarea especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener el nombre del estado de tarea
        estado_nombre = self.cultural_practice_repository.get_task_state_name(tarea_data.estado_id)
        if estado_nombre == self.COMPLETED_STATE_NAME:
            raise DomainException(
                message=f"No se puede crear una tarea directamente en estado '{self.COMPLETED_STATE_NAME}'.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Crear la tarea
        tarea = self.cultural_practice_repository.create_task(tarea_data)
        if not tarea:
            raise DomainException(
                message="No se pudo crear la tarea de labor cultural.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return SuccessTaskCreateResponse(message="Tarea creada exitosamente", task_id=tarea.id)

    def validate_tarea_data(self, tarea_data: TaskCreate):
        # Obtener la fecha actual
        current_date = get_current_date()

        # Validar que la fecha programada no esté en el pasado
        if tarea_data.fecha_inicio_estimada < current_date:
            raise DomainException(
                message="La fecha programada no puede ser anterior a la fecha actual.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
