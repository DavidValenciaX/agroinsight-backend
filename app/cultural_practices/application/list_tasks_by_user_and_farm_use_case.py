from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.domain.schemas import PaginatedTaskListResponse
from app.infrastructure.mappers.response_mappers import map_task_to_response
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from math import ceil
from app.user.infrastructure.sql_repository import UserRepository
from app.farm.application.services.farm_service import FarmService

class ListTasksByUserAndFarmUseCase:
    """Caso de uso para listar las tareas de un usuario en una finca específica.

    Este caso de uso gestiona la lógica de negocio para recuperar las tareas asignadas a un usuario
    en una finca específica, asegurando que se cumplan las validaciones necesarias antes de devolver
    la lista de tareas.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
        cultural_practice_repository (CulturalPracticesRepository): Repositorio para operaciones de prácticas culturales.
        user_repository (UserRepository): Repositorio para operaciones de usuarios.
        farm_service (FarmService): Servicio para lógica de negocio de fincas.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)
        self.user_repository = UserRepository(db)
        self.farm_service = FarmService(db)
        
    def list_tasks_by_user_and_farm(self, farm_id: int, user_id: int, page: int, per_page: int, current_user: UserInDB) -> PaginatedTaskListResponse:
        """Lista las tareas de un usuario en una finca específica de forma paginada.

        Este método valida que el usuario actual tenga permisos para acceder a las tareas del usuario
        especificado en la finca indicada. Si las validaciones son exitosas, devuelve una lista paginada
        de las tareas.

        Args:
            farm_id (int): ID de la finca de la que se desean listar las tareas.
            user_id (int): ID del usuario cuyas tareas se desean listar.
            page (int): Número de página para la paginación.
            per_page (int): Cantidad de tareas por página.
            current_user (UserInDB): Usuario actual autenticado que intenta acceder a las tareas.

        Returns:
            PaginatedTaskListResponse: Respuesta que contiene la lista paginada de tareas del usuario.

        Raises:
            DomainException: Si el usuario no tiene permisos, no existe, o no es trabajador de la finca.
        """
        # validar que el usuario es administrador de la finca
        if not self.farm_service.user_is_farm_admin(current_user.id, farm_id):
            raise DomainException(
                message="No tienes permisos para listar las tareas de este usuario.",
                status_code=status.HTTP_403_FORBIDDEN
            )
            
        # validar que el usuario existe
        if not self.user_repository.get_user_by_id(user_id):
            raise DomainException(
                message="El usuario especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        if current_user.id == user_id:
            raise DomainException(
                message="El usuario es el administrador de la finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # validar que el usuario pertenezca a la finca
        if not self.farm_service.user_is_farm_worker(user_id, farm_id):
            raise DomainException(
                message="El usuario no es trabajador en la finca especificada.",
                status_code=status.HTTP_403_FORBIDDEN
            )
            
        # listar las tareas del usuario filtradas por la finca
        total_tasks, tasks = self.cultural_practice_repository.list_tasks_by_user_and_farm_paginated(user_id, farm_id, page, per_page)

        task_responses = [map_task_to_response(task) for task in tasks]

        total_pages = ceil(total_tasks / per_page)

        return PaginatedTaskListResponse(
            tasks=task_responses,
            total_tasks=total_tasks,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
