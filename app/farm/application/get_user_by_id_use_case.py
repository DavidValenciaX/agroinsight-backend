from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.user.domain.schemas import UserResponse
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException, InsufficientPermissionsException, MissingTokenException, UserNotRegisteredException
from app.infrastructure.mappers.response_mappers import map_user_to_response
from fastapi import status

class AdminGetUserByIdUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.farm_repository = FarmRepository(db)
        
    def admin_get_user_by_id(self, user_id: int, farm_id: int, current_user) -> UserResponse:
        if not current_user:
            raise MissingTokenException()
        
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            raise UserNotRegisteredException()
        
        worker_role = self.user_repository.get_worker_role()
        
        # Verificar si el user_id es trabajador en la finca especificada
        if not self.farm_repository.user_is_farm_worker(user_id, farm_id):
            raise DomainException(
                message="El usuario no es trabajador en la finca especificada",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar si el current_user es administrador en la finca especificada
        if not self.farm_repository.user_is_farm_admin(current_user.id, farm_id):
            raise InsufficientPermissionsException()
        
        return map_user_to_response(user)
