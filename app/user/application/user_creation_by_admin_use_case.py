from sqlalchemy.orm import Session
from app.user.infrastructure.orm_models import User
from app.core.security.security_utils import hash_password
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.schemas import AdminUserCreate

class UserCreationByAdminUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def create_user_by_admin(self, user_data: AdminUserCreate) -> User:
        hashed_password = hash_password(user_data.password)
        active_state_id = self.user_repository.get_active_user_state_id()
        if not active_state_id:
            raise ValueError("No se pudo encontrar el estado de usuario activo")
        new_user = User(
            nombre=user_data.nombre,
            apellido=user_data.apellido,
            email=user_data.email,
            password=hashed_password,
            state_id=active_state_id
        )
        created_user = self.user_repository.create_user(new_user)
        # Asignar el rol especificado
        self.user_repository.assign_role_to_user(created_user.id, user_data.role_id)
        return created_user