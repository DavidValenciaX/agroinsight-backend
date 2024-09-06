# app/user/application/user_creation_use_case.py

from app.user.domain.user_entities import UserCreate
from app.user.infrastructure.user_orm_model import User as UserModel
from app.user.infrastructure.sql_user_repository import UserRepository
from app.core.security.security_utils import hash_password

class UserCreationUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, nombre: str, apellido: str, email: str, password: str):
        hashed_password = hash_password(password)
        
        # Obtener el estado activo
        active_state = self.user_repository.get_active_user_state()
        if not active_state:
            raise ValueError("No se pudo encontrar el estado de usuario activo")

        user_create = UserCreate(
            nombre=nombre,
            apellido=apellido,
            email=email,
            password=hashed_password,
            state_id=active_state.id
        )
        user_model = UserModel(**user_create.dict())
        created_user = self.user_repository.create_user(user_model)
        
        # Asignar el rol por defecto "Usuario"
        default_role = self.user_repository.get_default_role()
        if default_role:
            self.user_repository.assign_role_to_user(created_user.id, default_role.id)
        
        return created_user