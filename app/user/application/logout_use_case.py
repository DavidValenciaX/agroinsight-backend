from sqlalchemy.orm import Session
from app.infrastructure.common.response_models import SuccessResponse
from app.user.infrastructure.orm_models import BlacklistedToken
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class LogoutUseCase:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)
    
    def logout(self, token: str, user_id: int) -> SuccessResponse:
        success = self.blacklist_token(token, user_id)
        if not success:
            raise DomainException(
                message="No se pudo cerrar la sesión. Intenta nuevamente.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return SuccessResponse(
                message="Sesión cerrada exitosamente."
        )
        
    def blacklist_token(self, token: str, user_id: int) -> bool:
        blacklisted = BlacklistedToken(token=token, usuario_id=user_id)
        return self.user_repository.blacklist_token(blacklisted)
