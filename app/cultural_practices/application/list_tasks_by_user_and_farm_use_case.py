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
    def __init__(self, db: Session):
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)
        self.user_repository = UserRepository(db)
        self.farm_service = FarmService(db)
        
    def list_tasks_by_user_and_farm(self, farm_id: int, user_id: int, page: int, per_page: int, current_user: UserInDB) -> PaginatedTaskListResponse:
            
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
