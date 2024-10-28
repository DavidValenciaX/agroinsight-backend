from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.user.application.services.user_service import UserService
from app.user.infrastructure.sql_repository import UserRepository
from app.farm.application.services.farm_service import FarmService
from app.farm.domain.schemas import PaginatedFarmUserListResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from app.infrastructure.mappers.response_mappers import map_user_for_farm_to_response
from fastapi import status
from math import ceil

class ListFarmUsersUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.farm_repository = FarmRepository(db)
        self.user_repository = UserRepository(db)
        self.farm_service = FarmService(db)
        self.user_service = UserService(db)
        
    def list_farm_users(self, farm_id: int, current_user: UserInDB, page: int, per_page: int) -> PaginatedFarmUserListResponse:
        
        farm = self.farm_repository.get_farm_by_id(farm_id)
        if not farm:
            raise DomainException(
                message="La finca especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Verificar si current_user es administrador de la finca
        if not self.farm_service.user_is_farm_admin(current_user.id, farm_id):
            raise DomainException(
                message="No tienes permisos para obtener información de los usuarios de esta finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )
            
        worker_role = self.user_repository.get_role_by_name(self.user_service.WORKER_ROLE_NAME)

        total_users, users = self.farm_repository.list_farm_users_by_role_paginated(farm_id, worker_role.id, page, per_page)
        
        user_responses = []
        for user in users:
            # Obtener la relación usuario-finca
            user_farm = self.farm_repository.get_user_farm(user.id, farm_id)
            # Obtener el nombre del rol
            role_name = user_farm.rol.nombre
            # Mapear el usuario con su rol a la respuesta
            user_response = map_user_for_farm_to_response(user, role_name)
            user_responses.append(user_response)

        total_pages = ceil(total_users / per_page)

        return PaginatedFarmUserListResponse(
            users=user_responses,
            total_users=total_users,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
