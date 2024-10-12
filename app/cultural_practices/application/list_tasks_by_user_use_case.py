from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.domain.schemas import PaginatedTaskListResponse
from app.infrastructure.mappers.response_mappers import map_task_to_response
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from math import ceil

class ListTasksByUserUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)
        
    def list_tasks_by_user(self, user_id: int, page: int, per_page: int, current_user: UserInDB) -> PaginatedTaskListResponse:
        # Validar que el usuario existe
        if not self.cultural_practice_repository.user_exists(user_id):
            raise DomainException(
                message="El usuario especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        total_tasks, tasks = self.cultural_practice_repository.list_tasks_by_user_paginated(user_id, page, per_page)

        task_responses = [map_task_to_response(task) for task in tasks]

        total_pages = ceil(total_tasks / per_page)

        return PaginatedTaskListResponse(
            tasks=task_responses,
            total_tasks=total_tasks,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
