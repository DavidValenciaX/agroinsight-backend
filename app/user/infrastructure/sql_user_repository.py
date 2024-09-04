#app/user/infrastructure/sql_user_repository.py
from sqlalchemy.orm import Session
from app.user.domain.user_entities import UserInDB as UserDomain
from app.user.infrastructure.user_orm_model import User as UserModel
from app.user.domain.user_repository_interface import UserRepositoryInterface
from app.user.application.user_service import UserService

class UserRepository(UserRepositoryInterface):
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> UserDomain:
        user_model = self.db.query(UserModel).filter(UserModel.email == email).first()
        if user_model:
            return UserDomain(**user_model.__dict__)
        return None

    def update_user(self, user: UserDomain) -> UserDomain:
        user_model = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if user_model:
            for key, value in user.dict().items():
                setattr(user_model, key, value)
            self.db.commit()
            self.db.refresh(user_model)
            return UserDomain(**user_model.__dict__)
        return None

    def create_user(self, user: UserModel) -> UserDomain:
        user = UserService.hash_user_password(user)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return UserDomain.from_orm(user)