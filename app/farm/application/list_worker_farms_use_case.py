from sqlalchemy.orm import Session
from math import ceil
from app.farm.infrastructure.sql_repository import FarmRepository
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.schemas import UserInDB
from app.farm.domain.schemas import PaginatedWorkerFarmListResponse
from app.farm.application.services.farm_service import FarmService
from app.infrastructure.mappers.response_mappers import map_worker_farm_to_response
from fastapi import status

class ListWorkerFarmsUseCase:
    """Caso de uso para listar las fincas donde un usuario es trabajador.

    Esta clase maneja la lógica de negocio necesaria para obtener una lista paginada
    de las fincas donde un usuario específico tiene rol de trabajador.

    Attributes:
        db (Session): Sesión de base de datos.
        farm_repository (FarmRepository): Repositorio para operaciones con fincas.
        user_repository (UserRepository): Repositorio para operaciones con usuarios.
        farm_service (FarmService): Servicio para lógica de negocio de fincas.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        self.farm_repository = FarmRepository(db)
        self.user_repository = UserRepository(db)
        self.farm_service = FarmService(db)

    def list_worker_farms(self, current_user: UserInDB, page: int, per_page: int) -> PaginatedWorkerFarmListResponse:
        """Lista las fincas donde el usuario es trabajador de forma paginada.

        Este método realiza las siguientes operaciones:
        1. Obtiene el ID del rol de trabajador de finca.
        2. Filtra las fincas donde el usuario tiene rol de trabajador.
        3. Construye la respuesta paginada con la información de las fincas.

        Args:
            current_user (UserInDB): Usuario actual que solicita la lista de fincas.
            page (int): Número de página actual para la paginación.
            per_page (int): Cantidad de fincas por página.

        Returns:
            PaginatedWorkerFarmListResponse: Respuesta paginada que incluye:
                - Lista de fincas para la página actual
                - Total de fincas
                - Número de página actual
                - Elementos por página
                - Total de páginas
        """
        
        # Obtener id del rol de trabajador de finca
        worker_role = self.farm_service.get_worker_role()

        # Filtrar las fincas donde el usuario es trabajador
        total_farms, farms = self.farm_repository.list_farms_by_role_paginated(
            current_user.id, 
            worker_role.id, 
            page, 
            per_page
        )

        # Usar la función de mapeo para construir FarmResponse para cada finca
        farm_responses = [map_worker_farm_to_response(farm) for farm in farms]

        total_pages = ceil(total_farms / per_page)

        return PaginatedWorkerFarmListResponse(
            farms=farm_responses,
            total_farms=total_farms,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )