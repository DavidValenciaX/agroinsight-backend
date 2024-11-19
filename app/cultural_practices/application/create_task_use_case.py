from sqlalchemy.orm import Session
from app.cultural_practices.application.services.task_service import TaskService
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.domain.schemas import TaskCreate, SuccessTaskCreateResponse
from app.farm.application.services.farm_service import FarmService
from app.farm.infrastructure.sql_repository import FarmRepository
from app.plot.infrastructure.sql_repository import PlotRepository
from app.crop.infrastructure.sql_repository import CropRepository
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from app.cultural_practices.domain.schemas import NivelLaborCultural

class CreateTaskUseCase:
    """Caso de uso para crear tareas de labor cultural.

    Este caso de uso gestiona la lógica de negocio para la creación de tareas, asegurando que se cumplan
    las validaciones necesarias antes de realizar la creación.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
        cultural_practice_repository (CulturalPracticesRepository): Repositorio para operaciones de prácticas culturales.
        farm_repository (FarmRepository): Repositorio para operaciones de fincas.
        plot_repository (PlotRepository): Repositorio para operaciones de lotes.
        farm_service (FarmService): Servicio para lógica de negocio de fincas.
        task_service (TaskService): Servicio para lógica de negocio de tareas.
        crop_repository (CropRepository): Repositorio para operaciones de cultivos.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)
        self.farm_repository = FarmRepository(db)
        self.plot_repository = PlotRepository(db)
        self.farm_service = FarmService(db)
        self.task_service = TaskService(db)
        self.crop_repository = CropRepository(db)
        
    def create_task(self, task_data: TaskCreate, current_user: UserInDB) -> SuccessTaskCreateResponse:
        """Crea una nueva tarea de labor cultural.

        Este método valida la existencia del lote, el cultivo activo en el lote, la finca asociada,
        y los permisos del usuario que intenta crear la tarea. Si todas las validaciones son exitosas,
        se crea la tarea.

        Args:
            task_data (TaskCreate): Datos de la tarea a crear.
            current_user (UserInDB): Usuario actual autenticado que intenta crear la tarea.

        Returns:
            SuccessTaskCreateResponse: Respuesta que indica que la tarea fue creada exitosamente.

        Raises:
            DomainException: Si el lote, la finca, el cultivo activo, el tipo de labor cultural o el estado de tarea no son válidos.
        """
        plot = self.plot_repository.get_plot_by_id(task_data.lote_id)
        if not plot:
            raise DomainException(
                message="No se pudo obtener el lote.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Validar que el lote tiene un cultivo activo
        if not self.crop_repository.has_active_crop(task_data.lote_id):
            raise DomainException(
                message="El lote no tiene un cultivo activo. No se pueden crear tareas en lotes sin cultivos activos.",
                status_code=status.HTTP_409_CONFLICT
            )
        
        # Buscar el id de la finca por medio del id del lote
        farm = self.farm_repository.get_farm_by_id(plot.finca_id)
        if not farm:
            raise DomainException(
                message="No se pudo obtener la finca.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Validar que el usuario sea administrador de la finca
        if not self.farm_service.user_is_farm_admin(current_user.id, farm.id):
            raise DomainException(
                message="No tienes permisos para crear tareas en esta finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar si el tipo de labor cultural existe
        task_type = self.cultural_practice_repository.get_task_type_by_id(task_data.tipo_labor_id)
        if not task_type:
            raise DomainException(
                message="El tipo de labor cultural especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Obtener el cultivo activo del lote si el tipo de labor es a nivel de CULTIVO
        if task_type.nivel == NivelLaborCultural.CULTIVO:
            active_crop = self.crop_repository.get_active_crop_by_plot_id(task_data.lote_id)
            if not active_crop:
                raise DomainException(
                    message="No se pueden crear tareas de nivel CULTIVO en lotes sin cultivos activos.",
                    status_code=status.HTTP_409_CONFLICT
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
