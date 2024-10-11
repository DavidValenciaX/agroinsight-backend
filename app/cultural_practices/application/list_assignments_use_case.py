from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.domain.schemas import PaginatedAssignmentListResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException, InsufficientPermissionsException
from app.infrastructure.mappers.response_mappers import map_assignment_to_response
from fastapi import status
from math import ceil

from app.user.infrastructure.sql_repository import UserRepository
from app.farm.infrastructure.sql_repository import FarmRepository

class ListAssignmentsUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)
        self.user_repository = UserRepository(db)
        self.farm_repository = FarmRepository(db)
        
    def list_assignments(self, user_id: int, page: int, per_page: int, current_user: UserInDB) -> PaginatedAssignmentListResponse:
        # Validar que el usuario existe
        if not self.user_repository.user_exists(user_id):
            raise DomainException(
                message="El usuario especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Obtener las fincas donde el usuario es trabajador
        worker_farm_ids = self.farm_repository.get_farms_where_user_is_worker(user_id)

        # Filtrar las fincas donde el current_user es administrador
        admin_farm_ids = [farm_id for farm_id in worker_farm_ids if self.farm_repository.user_is_farm_admin(current_user.id, farm_id)]

        if not admin_farm_ids:
            raise InsufficientPermissionsException()

        total_assignments, assignments = self.cultural_practice_repository.list_assignments_by_user_paginated(user_id, page, per_page, admin_farm_ids)

        assignment_responses = [map_assignment_to_response(assignment) for assignment in assignments]

        total_pages = ceil(total_assignments / per_page)

        return PaginatedAssignmentListResponse(
            assignments=assignment_responses,
            total_assignments=total_assignments,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )