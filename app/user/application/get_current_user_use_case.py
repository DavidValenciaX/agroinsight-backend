from sqlalchemy.orm import Session
from app.infrastructure.mappers.response_mappers import map_user_to_response
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.schemas import UserResponse
from app.infrastructure.common.common_exceptions import MissingTokenException, UserStateException
from fastapi import status

class GetCurrentUserUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def execute(self, current_user) -> UserResponse:
        if not current_user:
            raise MissingTokenException()
            
        # Obtener el estado del usuario
        estado = self.user_repository.get_state_by_id(current_user.state_id)
        if not estado:
            raise UserStateException(
                message="Estado de usuario no reconocido.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                user_state="unknown"
            )
        
        current_user.estado = estado
        return map_user_to_response(current_user)