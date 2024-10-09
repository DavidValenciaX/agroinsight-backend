# app/farm/application/list_farms_use_case.py
from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.farm.domain.schemas import PaginatedFarmListResponse
from app.user.domain.schemas import UserInDB, UserResponse
from app.infrastructure.common.common_exceptions import InsufficientPermissionsException
from app.infrastructure.mappers.response_mappers import map_farm_to_response
from fastapi import status
from math import ceil

class ListFarmsUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.farm_repository = FarmRepository(db)

    def list_farms(self, current_user: UserInDB, page: int, per_page: int) -> PaginatedFarmListResponse:
        if not self.user_can_list_farms(current_user):
            raise InsufficientPermissionsException()

        total_farms, farms = self.farm_repository.list_farms_paginated(current_user.id, page, per_page)

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

    def user_can_list_farms(self, user: UserInDB) -> bool:
        # Verificar si el usuario tiene el rol de "Administrador de Finca" en alguna finca
        return any(role.rol.nombre == "Administrador de Finca" for role in user.roles_fincas)