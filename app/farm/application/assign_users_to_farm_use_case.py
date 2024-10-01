from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.user.infrastructure.sql_repository import UserRepository
from app.farm.domain.schemas import FarmUserAssignment, FarmUserAssignmentResponse
from app.user.domain.schemas import SuccessResponse, UserInDB
from app.infrastructure.common.common_exceptions import DomainException, InsufficientPermissionsException
from fastapi import status

class AssignUsersToFarmUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.farm_repository = FarmRepository(db)
        self.user_repository = UserRepository(db)

    def execute(self, assignment_data: FarmUserAssignment, current_user: UserInDB) -> SuccessResponse:
        if not self.user_can_assign_users(current_user):
            raise InsufficientPermissionsException()

        farm = self.farm_repository.get_farm_by_id(assignment_data.farm_id)
        if not farm:
            raise DomainException(
                message="La finca especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        for user_id in assignment_data.user_ids:
            user = self.user_repository.get_user_by_id(user_id)
            if not user:
                raise DomainException(
                    message=f"El usuario con ID {user_id} no existe.",
                    status_code=status.HTTP_404_NOT_FOUND
                )

        self.farm_repository.assign_users_to_farm(assignment_data.farm_id, assignment_data.user_ids)

        return SuccessResponse(
            message="Usuarios asignados exitosamente a la finca."
        )

    def user_can_assign_users(self, user: UserInDB) -> bool:
        allowed_roles = ["Superusuario", "Administrador de Finca"]
        return any(role.nombre in allowed_roles for role in user.roles)