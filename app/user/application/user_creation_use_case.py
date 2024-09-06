#app/user/application/user_creation_use_case.py
from app.user.domain.user_entities import UserCreate
from app.user.infrastructure.user_orm_model import User as UserModel
from app.user.infrastructure.sql_user_repository import UserRepository
from app.core.security.security_utils import hash_password

class UserCreationUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, nombre: str, apellido: str, email: str, password: str, state_id: int = 1):
        hashed_password = hash_password(password)
        user_create = UserCreate(
            nombre=nombre,
            apellido=apellido,
            email=email,
            password=hashed_password,
            state_id=state_id
        )
        user_model = UserModel(**user_create.dict())
        created_user = self.user_repository.create_user(user_model)
        
        # Asignar el rol por defecto "Usuario"
        default_role = self.user_repository.get_default_role()
        if default_role:
            self.user_repository.assign_role_to_user(created_user.id, default_role.id)
        
        return created_user