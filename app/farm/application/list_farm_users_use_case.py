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

    def list_farm_users(self, farm_id: int, role_name: Optional[str], role_id: Optional[int], current_user: UserInDB, page: int, per_page: int) -> PaginatedFarmUserListResponse:
        self.validate_params(page, per_page)
        
        if not self.user_can_list_farm_users(current_user, farm_id):
            raise InsufficientPermissionsException()

        farm = self.farm_repository.get_farm_by_id(farm_id)
        if not farm:
            raise DomainException(
                message="La finca especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        role = self.get_role(role_name, role_id)

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

    def get_role(self, role_name: Optional[str], role_id: Optional[int]):
        if role_name:
            role = self.user_repository.get_role_by_name(role_name)
            if not role:
                raise DomainException(
                    message=f"El rol '{role_name}' no existe.",
                    status_code=status.HTTP_404_NOT_FOUND
                )
        elif role_id:
            role = self.user_repository.get_role_by_id(role_id)
            if not role:
                raise DomainException(
                    message=f"El rol con ID '{role_id}' no existe.",
                    status_code=status.HTTP_404_NOT_FOUND
                )
        else:
            raise DomainException(
                message="Debe proporcionar un nombre de rol o un ID de rol.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        return role

    def user_can_list_farm_users(self, user: UserInDB, farm_id: int) -> bool:
        allowed_roles = ["Administrador de Finca"]
        has_allowed_role = any(role.nombre in allowed_roles for role in user.roles)
        
        # Si es Administrador de Finca, verificar si está vinculado a la finca
        if has_allowed_role:
            return self.farm_repository.user_has_access_to_farm(user.id, farm_id)
        
        return False

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