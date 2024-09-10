from app.user.domain.user_entities import UserCreate
from app.user.infrastructure.user_orm_model import User as UserModel
from app.user.infrastructure.sql_user_repository import UserRepository
from app.core.security.security_utils import hash_password

class UserCreationUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, nombre: str, apellido: str, email: str, password: str) -> UserModel:
        hashed_password = hash_password(password)
        
        # Obtener el estado pendiente
        pending_state = self.user_repository.get_pending_user_state()
        if not pending_state:
            raise ValueError("No se pudo encontrar el estado de usuario pendiente")

        user_create = UserCreate(
            nombre=nombre,
            apellido=apellido,
            email=email,
            password=hashed_password,
            state_id=pending_state.id
        )
        user_model = UserModel(**user_create.dict())
        created_user = self.user_repository.create_user(user_model)
        
        # Asignar el rol "Usuario No Confirmado"
        unconfirmed_role = self.user_repository.get_unconfirmed_user_role()
        if unconfirmed_role:
            self.user_repository.assign_role_to_user(created_user.id, unconfirmed_role.id)
        else:
            raise ValueError("No se pudo encontrar el rol de Usuario No Confirmado")
        
        return created_user  # Esto debería ser una instancia de UserModel