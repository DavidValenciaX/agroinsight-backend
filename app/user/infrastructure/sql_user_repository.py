from sqlalchemy.orm import Session
from app.user.domain.user_entities import UserInDB as UserDomain
from app.user.infrastructure.user_orm_model import User as UserModel
from app.user.domain.user_repository_interface import UserRepositoryInterface
from app.user.infrastructure.estado_usuario_orm_model import EstadoUsuario
from app.user.infrastructure.role_orm_model import Role
from app.user.infrastructure.user_role_orm_model import UserRole

class UserRepository(UserRepositoryInterface):
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> UserDomain:
        user_model = self.db.query(UserModel).filter(UserModel.email == email).first()
        if user_model:
            return UserDomain.from_orm(user_model)
        return None

    def update_user(self, user: UserDomain) -> UserDomain:
        user_model = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if user_model:
            for key, value in user.dict().items():
                setattr(user_model, key, value)
            self.db.commit()
            self.db.refresh(user_model)
            return UserDomain.from_orm(user_model)
        return None
    
    def create_user(self, user: UserModel) -> UserDomain:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return UserDomain.from_orm(user)
    
    def get_active_user_state(self):
        return self.db.query(EstadoUsuario).filter(EstadoUsuario.nombre == "active").first()

    def get_pending_user_state(self):
        return self.db.query(EstadoUsuario).filter(EstadoUsuario.nombre == "pending").first()

    def get_default_role(self):
        return self.db.query(Role).filter(Role.nombre == "Usuario").first()

    def get_unconfirmed_user_role(self):
        return self.db.query(Role).filter(Role.nombre == "Usuario No Confirmado").first()

    def assign_role_to_user(self, user_id: int, role_id: int):
        user_role = UserRole(usuario_id=user_id, rol_id=role_id)
        self.db.add(user_role)
        self.db.commit()