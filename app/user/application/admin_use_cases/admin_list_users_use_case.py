from typing import List
from sqlalchemy.orm import Session
from app.infrastructure.common.common_exceptions import InsufficientPermissionsException, MissingTokenException
from app.user.domain.schemas import UserResponse
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.mappers.response_mappers import map_user_to_response

class AdminListUsersUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def admin_list_users(self, current_user) -> List[UserResponse]:
        if not current_user:
            raise MissingTokenException()
        
        users = self.user_repository.get_all_users()
        if not users:
            return []  # Retornar lista vacía
        
        # Usar la función de mapeo para construir UserResponse para cada usuario
        return [map_user_to_response(user) for user in users]
