# app/farm/application/list_farms_use_case.py
from sqlalchemy.orm import Session
from app.farm.application.services.farm_service import FarmService
from app.farm.infrastructure.sql_repository import FarmRepository
from app.farm.domain.schemas import PaginatedFarmListResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.mappers.response_mappers import map_farm_to_response
from math import ceil
from app.user.infrastructure.orm_models import Role
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

from app.user.application.services.user_service import UserService

class ListFarmsUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.farm_repository = FarmRepository(db)
        self.user_repository = UserRepository(db)
        self.user_service = UserService(db)
        self.farm_service = FarmService(db)
        
    def list_farms(self, current_user: UserInDB, page: int, per_page: int) -> PaginatedFarmListResponse:
        
        # Obtener id del rol de administrador de finca
        admin_role = self.farm_service.get_admin_role()

        # Filtrar las fincas donde el usuario es administrador
        total_farms, farms = self.farm_repository.list_farms_by_role_paginated(current_user.id, admin_role.id, page, per_page)

        # Usar la función de mapeo para construir FarmResponse para cada finca
        farm_responses = [map_farm_to_response(farm) for farm in farms]

        total_pages = ceil(total_farms / per_page)

        return PaginatedFarmListResponse(
            farms=farm_responses,
            total_farms=total_farms,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )