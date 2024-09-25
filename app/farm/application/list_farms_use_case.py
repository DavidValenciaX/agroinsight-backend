from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.farm.domain.schemas import FarmListResponse, FarmResponse, PaginatedFarmListResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from math import ceil

class ListFarmsUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.farm_repository = FarmRepository(db)

    def execute(self, current_user: UserInDB, page: int, per_page: int) -> PaginatedFarmListResponse:
        if not self.user_can_list_farms(current_user):
            raise DomainException(
                message="No tienes permisos para listar fincas.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        total_farms, farms = self.farm_repository.list_farms_paginated(current_user.id, page, per_page)

        farm_responses = [
            FarmResponse(
                id=farm.id,
                nombre=farm.nombre,
                ubicacion=farm.ubicacion,
                area_total=farm.area_total,
                unidad_area=farm.unidad_area.abreviatura,
                latitud=farm.latitud,
                longitud=farm.longitud
            ) for farm in farms
        ]

        total_pages = ceil(total_farms / per_page)

        return PaginatedFarmListResponse(
            farms=farm_responses,
            total_farms=total_farms,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )

    def user_can_list_farms(self, user: UserInDB) -> bool:
        allowed_roles = ["Superusuario", "Administrador de finca", "Usuario"]
        return any(role.nombre in allowed_roles for role in user.roles)