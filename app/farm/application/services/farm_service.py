from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.user.application.services.user_service import UserService
from app.user.infrastructure.sql_repository import UserRepository


class FarmService:
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.user_service = UserService(db)
        self.farm_repository = FarmRepository(db)

    def user_is_farm_admin(self, user_id: int, farm_name: str) -> bool:
        admin_role = self.user_repository.get_role_by_name(self.user_service.ADMIN_ROLE_NAME)
        if not admin_role:
            return False
        
        farm = self.farm_repository.get_farm_by_name(farm_name)
        if not farm:
            return False
        
        return self.farm_repository.get_user_farm_role(user_id, farm.id, admin_role.id) is not None