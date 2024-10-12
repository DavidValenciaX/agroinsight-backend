from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.user.infrastructure.sql_repository import UserRepository
from app.farm.domain.schemas import PaginatedFarmUserListResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException, InsufficientPermissionsException
from app.infrastructure.mappers.response_mappers import map_user_to_response
from fastapi import status
from math import ceil
from typing import Optional

class ListFarmUsersUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.farm_repository = FarmRepository(db)
        self.user_repository = UserRepository(db)

    def list_farm_users(self, farm_id: int, role_id: int, current_user: UserInDB, page: Optional[int], per_page: Optional[int]) -> PaginatedFarmUserListResponse:
        self.validate_params(page, per_page)
        
        farm = self.farm_repository.get_farm_by_id(farm_id)
        if not farm:
            raise DomainException(
                message="La finca especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Verificar si current_user es administrador de la finca
        if not self.farm_repository.user_is_farm_admin(current_user.id, farm_id):
            raise DomainException(
                message="No tienes permisos para obtener información de los usuarios de esta finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        role = self.user_repository.get_role_by_id(role_id)
        if not role:
            raise DomainException(
                message=f"El rol con ID '{role_id}' no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        total_users, users = self.farm_repository.list_farm_users_by_role_paginated(farm_id, role.id, page, per_page)

        user_responses = [map_user_to_response(user) for user in users]

        total_pages = ceil(total_users / per_page)

        return PaginatedFarmUserListResponse(
            users=user_responses,
            total_users=total_users,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )

    def validate_params(self, page: int, per_page: int):
        if page < 1:
            raise DomainException(
                message="El número de página debe ser mayor o igual a 1.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        if per_page < 1 or per_page > 100:
            raise DomainException(
                message="El número de elementos por página debe estar entre 1 y 100.",
                status_code=status.HTTP_400_BAD_REQUEST
            )