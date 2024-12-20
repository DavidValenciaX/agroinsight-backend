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
from app.infrastructure.common.datetime_utils import datetime_utc_time
from typing import Union
from app.cultural_practices.domain.schemas import TaskStateResponse

class ChangeTaskStateUseCase:
    """Caso de uso para cambiar el estado de una tarea de labor cultural.

    Este caso de uso gestiona la lógica de negocio para cambiar el estado de una tarea,
    asegurando que se cumplan las validaciones necesarias antes de realizar el cambio.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
        cultural_practice_repository (CulturalPracticesRepository): Repositorio para operaciones de prácticas culturales.
        plot_repository (PlotRepository): Repositorio para operaciones de lotes.
        farm_repository (FarmRepository): Repositorio para operaciones de fincas.
        farm_service (FarmService): Servicio para lógica de negocio de fincas.
        task_service (TaskService): Servicio para lógica de negocio de tareas.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)
        self.plot_repository = PlotRepository(db)
        self.farm_repository = FarmRepository(db)
        self.farm_service = FarmService(db)
        self.task_service = TaskService(db)
        
    def change_task_state(self, task_id: int, state_id: Union[int, str], current_user: UserInDB) -> SuccessResponse:
        """Cambia el estado de una tarea de labor cultural.

        Args:
            task_id (int): ID de la tarea cuyo estado se desea cambiar.
            state_id (Union[int, str]): ID del estado o comando ('in_progress', 'done').
            current_user (UserInDB): Usuario actual autenticado que intenta cambiar el estado.

        Returns:
            SuccessResponse: Respuesta que indica que el estado de la tarea fue cambiado exitosamente.

        Raises:
            DomainException: Si la tarea, el estado, o los permisos del usuario no son válidos.
        """
        # Validar existencia de la tarea
        if not self.cultural_practice_repository.get_task_by_id(task_id):
            raise DomainException(
                message="La tarea especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Validar permisos del usuario
        if not self.user_can_change_task_state(current_user.id, task_id):
            raise DomainException(
                message="No tienes permisos para cambiar el estado de esta tarea.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Intentar convertir state_id a entero
        try:
            numeric_state_id = int(state_id)
        except ValueError:
            # Si falla, intentar convertir comando de texto a ID
            numeric_state_id = self.task_service.get_state_id_from_command(state_id)
            if numeric_state_id is None:
                raise DomainException(
                    message="Comando de estado inválido. Use un ID numérico o 'in_progress'/'done'.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        # Obtener el estado objetivo
        target_state: TaskStateResponse = self.cultural_practice_repository.get_task_state_by_id(numeric_state_id)
        if not target_state:
            raise DomainException(
                message="No se pudo obtener el estado al cuál se quiere cambiar la tarea.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Obtener tarea por ID
        task = self.cultural_practice_repository.get_task_by_id(task_id)
        if not task:
            raise DomainException(
                message="No se pudo obtener la tarea.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Actualizar el estado de la tarea
        task.estado_id = numeric_state_id
        task.estado = target_state

        # Actualizar la fecha de finalización si es necesario
        if target_state.nombre == TaskService.COMPLETADA:
            task.fecha_finalizacion = datetime_utc_time()
        else:
            task.fecha_finalizacion = None

        # Guardar cambios en la base de datos
        if not self.cultural_practice_repository.update_task(task):
            raise DomainException(
                message="No se pudo actualizar el estado de la tarea.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return SuccessResponse(
            message=f"Estado de la tarea cambiado exitosamente a '{target_state.nombre}'."
        )
    
    def user_can_change_task_state(self, user_id: int, task_id: int) -> bool:
        """Verifica si un usuario tiene permisos para cambiar el estado de una tarea.

        Este método valida la existencia de la tarea, el lote y la finca asociada, y verifica si el usuario
        es administrador o trabajador de la finca.

        Args:
            user_id (int): ID del usuario que intenta cambiar el estado.
            task_id (int): ID de la tarea cuyo estado se desea cambiar.

        Returns:
            bool: True si el usuario tiene permisos para cambiar el estado, False en caso contrario.

        Raises:
            DomainException: Si la tarea, el lote o la finca no existen.
        """
        # Obtener tarea por ID
        task = self.cultural_practice_repository.get_task_by_id(task_id)
        if not task:
            raise DomainException(
                message="No se pudo obtener la tarea.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Obtener lote por ID
        plot = self.plot_repository.get_plot_by_id(task.lote_id)
        if not plot:
            raise DomainException(
                message="No se pudo obtener el lote.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Obtener finca por ID
        farm = self.farm_repository.get_farm_by_id(plot.finca_id)
        if not farm:
            raise DomainException(
                message="No se pudo obtener la finca.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Verificar si el usuario es administrador o trabajador de la finca
        return (self.farm_service.user_is_farm_admin(user_id, farm.id) or 
                self.farm_service.user_is_farm_worker(user_id, farm.id))