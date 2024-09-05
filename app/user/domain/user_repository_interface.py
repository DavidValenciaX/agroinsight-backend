#app/user/domain/user_repository_interface.py
from abc import ABC, abstractmethod
from .user_entities import UserInDB

class UserRepositoryInterface(ABC):
    @abstractmethod
    def get_user_by_email(self, email: str) -> UserInDB:
        pass

    @abstractmethod
    def update_user(self, user: UserInDB) -> UserInDB:
        pass