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
        
    def admin_get_user_by_id(self, user_id: int, current_user) -> UserResponse:
        if not current_user:
            raise MissingTokenException()
        
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            raise UserNotRegisteredException()
        
        worker_role = self.farm_repository.get_worker_role()
        
        #obtener las fincas donde el usuario es trabajador 
        user_farms = self.farm_repository.get_farms_by_user_role(user_id, worker_role.id)
        if not user_farms:
            raise DomainException(
                message="El usuario no está asignado a ninguna finca",
                status_code=status.HTTP_400_BAD_REQUEST
                )
        
        # Verificar si el current_user es administrador en las fincas donde el user es trabajador
        for farm in user_farms:
            if self.farm_repository.user_is_farm_admin(current_user.id, farm):
                return map_user_to_response(user)
            
        raise InsufficientPermissionsException()
