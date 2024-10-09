from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.domain.schemas import PaginatedAssignmentListResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException, InsufficientPermissionsException
from app.infrastructure.mappers.response_mappers import map_assignment_to_response
from fastapi import status
from math import ceil

class ListAssignmentsUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)

    def list_assignments(self, user_id: int, page: int, per_page: int, current_user: UserInDB) -> PaginatedAssignmentListResponse:
        if not self.user_can_list_assignments(current_user):
            raise InsufficientPermissionsException()

        if not self.cultural_practice_repository.user_exists(user_id):
            raise DomainException(
                message="El usuario especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        total_assignments, assignments = self.cultural_practice_repository.list_assignments_by_user_paginated(user_id, page, per_page)

        assignment_responses = [map_assignment_to_response(assignment) for assignment in assignments]

        total_pages = ceil(total_assignments / per_page)

        return PaginatedAssignmentListResponse(
            assignments=assignment_responses,
            total_assignments=total_assignments,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )

    def user_can_list_assignments(self, user: UserInDB) -> bool:
        allowed_roles = ["Administrador de Finca"]
        return any(role.nombre in allowed_roles for role in user.roles)