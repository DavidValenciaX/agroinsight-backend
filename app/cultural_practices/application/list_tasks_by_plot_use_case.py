from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.domain.schemas import PaginatedTaskListResponse
from app.infrastructure.mappers.response_mappers import map_task_to_response
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from math import ceil
from app.farm.application.services.farm_service import FarmService
from app.plot.infrastructure.sql_repository import PlotRepository

class ListTasksByPlotUseCase:
    """Caso de uso para listar las tareas de un lote específico.

    Este caso de uso gestiona la lógica de negocio para recuperar las tareas asignadas a un lote
    específico, asegurando que se cumplan las validaciones necesarias antes de devolver la lista
    de tareas.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
        cultural_practice_repository (CulturalPracticesRepository): Repositorio para operaciones de prácticas culturales.
        plot_repository (PlotRepository): Repositorio para operaciones de lotes.
        farm_service (FarmService): Servicio para lógica de negocio de fincas.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias."""
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)
        self.plot_repository = PlotRepository(db)
        self.farm_service = FarmService(db)

    def list_tasks_by_plot(self, farm_id: int, plot_id: int, page: int, per_page: int, current_user: UserInDB) -> PaginatedTaskListResponse:
        """Lista las tareas de un lote específico de forma paginada.

        Args:
            farm_id (int): ID de la finca.
            plot_id (int): ID del lote.
            page (int): Número de página para la paginación.
            per_page (int): Cantidad de elementos por página.
            current_user (UserInDB): Usuario actual autenticado.

        Returns:
            PaginatedTaskListResponse: Lista paginada de tareas del lote.

        Raises:
            DomainException: Si el lote no existe, no pertenece a la finca o el usuario no tiene permisos.
        """
        # Validar que el lote existe
        plot = self.plot_repository.get_plot_by_id(plot_id)
        if not plot:
            raise DomainException(
                message="El lote especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Validar que el lote pertenece a la finca especificada
        if plot.finca_id != farm_id:
            raise DomainException(
                message="El lote no pertenece a la finca especificada.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Validar que el usuario tiene permisos (es admin de la finca)
        if not (self.farm_service.user_is_farm_admin(current_user.id, farm_id)):
            raise DomainException(
                message="No tienes permisos para ver las tareas de este lote.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Obtener las tareas del lote
        total_tasks, tasks = self.cultural_practice_repository.list_tasks_by_plot_paginated(
            plot_id, 
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