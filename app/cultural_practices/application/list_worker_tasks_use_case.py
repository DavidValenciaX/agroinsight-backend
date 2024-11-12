from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.domain.schemas import PaginatedTaskListResponse
from app.infrastructure.mappers.response_mappers import map_task_to_response
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from math import ceil
from app.farm.application.services.farm_service import FarmService

class ListWorkerTasksUseCase:
    """Caso de uso para listar las tareas asignadas a un trabajador.

    Este caso de uso permite a un trabajador ver sus propias tareas asignadas en una finca específica.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
        cultural_practice_repository (CulturalPracticesRepository): Repositorio para operaciones de prácticas culturales.
        farm_service (FarmService): Servicio para lógica de negocio de fincas.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias."""
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)
        self.farm_service = FarmService(db)
        
    def list_worker_tasks(self, farm_id: int, page: int, per_page: int, current_user: UserInDB) -> PaginatedTaskListResponse:
        """Lista las tareas asignadas a un trabajador en una finca específica.

        Args:
            farm_id (int): ID de la finca.
            page (int): Número de página para la paginación.
            per_page (int): Cantidad de elementos por página.
            current_user (UserInDB): Usuario actual (trabajador).

        Returns:
            PaginatedTaskListResponse: Lista paginada de tareas asignadas al trabajador.

        Raises:
            DomainException: Si el usuario no es trabajador de la finca o si hay algún error.
        """
        # Validar que el usuario sea trabajador de la finca
        if not self.farm_service.user_is_farm_worker(current_user.id, farm_id):
            raise DomainException(
                message="No eres trabajador de esta finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )
            
        # Obtener las tareas del trabajador
        total_tasks, tasks = self.cultural_practice_repository.list_tasks_by_user_and_farm_paginated(
            current_user.id, 
            farm_id, 
            page, 
            per_page
        )

        task_responses = [map_task_to_response(task) for task in tasks]
        total_pages = ceil(total_tasks / per_page)

        return PaginatedTaskListResponse(
            tasks=task_responses,
            total_tasks=total_tasks,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        ) 