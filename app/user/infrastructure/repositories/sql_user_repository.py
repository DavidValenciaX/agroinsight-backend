from sqlalchemy.orm import Session, joinedload
from app.user.domain.user_entities import UserInDB, RoleInfo
from app.user.infrastructure.orm_models.user_orm_model import User as UserModel
from app.user.infrastructure.orm_models.user_state_orm_model import EstadoUsuario
from app.user.infrastructure.orm_models.role_orm_model import Role
from app.user.infrastructure.orm_models.user_role_orm_model import UserRole
from datetime import datetime, timezone, timedelta

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> UserInDB:
        user_model = self.db.query(UserModel).options(joinedload(UserModel.roles)).filter(UserModel.email == email).first()
        if user_model:
            roles = [RoleInfo(id=role.id, nombre=role.nombre) for role in user_model.roles]
            return UserInDB(
                id=user_model.id,
                nombre=user_model.nombre,
                apellido=user_model.apellido,
                email=user_model.email,
                password=user_model.password,
                failed_attempts=user_model.failed_attempts,
                locked_until=user_model.locked_until,
                state_id=user_model.state_id,
                roles=roles
            )
        return None

    def update_user(self, user: UserInDB) -> UserInDB:
        user_model = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if user_model:
            user_model.nombre = user.nombre
            user_model.apellido = user.apellido
            user_model.email = user.email
            user_model.password = user.password
            user_model.failed_attempts = user.failed_attempts
            user_model.locked_until = user.locked_until
            user_model.state_id = user.state_id
            
            self.db.commit()
            self.db.refresh(user_model)
            return self.get_user_by_email(user_model.email)
        return None
    
    def create_user(self, user: UserModel) -> UserModel:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def block_user(self, user_id: int, lock_duration: timedelta):
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if user:
            user.locked_until = datetime.now(timezone.utc) + lock_duration
            user.state_id = 3  # Estado bloqueado
            self.db.commit()
            return True
        return False
    
    def unblock_user(self, user_id: int):
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if user:
            user.locked_until = None
            user.state_id = 1  # Estado activo
            user.failed_attempts = 0
            self.db.commit()
            return True
        return False
    
    def get_state_by_id(self, state_id: int):
        return self.db.query(EstadoUsuario).filter(EstadoUsuario.id == state_id).first()
    
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
        
    def change_user_role(self, user_id: int, old_role_name: str, new_role_name: str):
        old_role = self.db.query(Role).filter(Role.nombre == old_role_name).first()
        new_role = self.db.query(Role).filter(Role.nombre == new_role_name).first()

        if old_role and new_role:
            user_role = self.db.query(UserRole).filter(
                UserRole.usuario_id == user_id,
                UserRole.rol_id == old_role.id
            ).first()

            if user_role:
                user_role.rol_id = new_role.id
                self.db.commit()
                return True

        return False