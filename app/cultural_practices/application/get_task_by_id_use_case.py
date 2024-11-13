from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.domain.schemas import TaskResponse
from app.farm.application.services.farm_service import FarmService
from app.farm.infrastructure.sql_repository import FarmRepository
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from app.user.domain.schemas import UserInDB

class GetTaskByIdUseCase:
    """Caso de uso para obtener una tarea de labor cultural por su ID.

    Este caso de uso gestiona la lógica de negocio para recuperar una tarea específica,
    asegurando que se cumplan las validaciones necesarias antes de devolver la tarea.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
        cultural_practice_repository (CulturalPracticesRepository): Repositorio para operaciones de prácticas culturales.
        farm_service (FarmService): Servicio para lógica de negocio de fincas.
        farm_repository (FarmRepository): Repositorio para operaciones de fincas.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)
        self.farm_service = FarmService(db)
        self.farm_repository = FarmRepository(db)
        
    def get_task_by_id(self, farm_id: int, task_id: int, current_user: UserInDB) -> TaskResponse:
        """Obtiene una tarea de labor cultural por su ID.

        Este método valida la existencia de la tarea y verifica si el usuario tiene permisos
        para acceder a la tarea. Si las validaciones son exitosas, devuelve la tarea.

        Args:
            farm_id (int): ID de la finca a la que pertenece la tarea.
            task_id (int): ID de la tarea que se desea obtener.
            current_user (UserInDB): Usuario actual autenticado que intenta acceder a la tarea.

        Returns:
            TaskResponse: Respuesta que contiene los detalles de la tarea.

        Raises:
            DomainException: Si la tarea no existe o si el usuario no tiene permisos para acceder a ella.
        """
        # Validar que la tarea existe
        task = self.cultural_practice_repository.get_task_by_id(task_id)
        if not task:
            raise DomainException(
                message="La tarea especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Validar que el usuario es el administrador de la finca
        if not self.farm_service.user_is_farm_admin(current_user.id, farm_id):
            raise DomainException(
                message="No tienes permisos para acceder a esta tarea.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        return TaskResponse(
            id=task.id,
            nombre=task.nombre,
            tipo_labor_id=task.tipo_labor_id,
            tipo_labor_nombre=task.tipo_labor.nombre,
            fecha_inicio_estimada=task.fecha_inicio_estimada,
            fecha_finalizacion=task.fecha_finalizacion,
            descripcion=task.descripcion,
            estado_id=task.estado_id,
            estado_nombre=task.estado.nombre,
            lote_id=task.lote_id
        )

