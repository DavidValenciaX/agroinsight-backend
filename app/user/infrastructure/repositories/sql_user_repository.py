from sqlalchemy.orm import Session, joinedload
from app.user.domain.user_entities import UserInDB, RoleInfo
from app.user.infrastructure.orm_models.user_orm_model import User
from app.user.infrastructure.orm_models.user_state_orm_model import EstadoUsuario
from app.user.infrastructure.orm_models.role_orm_model import Role
from app.user.infrastructure.orm_models.user_role_orm_model import UserRole
from app.user.infrastructure.orm_models.password_recovery_orm_model import RecuperacionContrasena
from app.user.infrastructure.orm_models.two_factor_verify_orm_model import VerificacionDospasos
from app.user.infrastructure.orm_models.user_confirmation_orm_model import ConfirmacionUsuario
from datetime import datetime, timezone, timedelta

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    # Métodos relacionados con el usuario
    def get_user_by_email(self, email: str) -> UserInDB:
        # Usamos joinedload para cargar la relación muchos a muchos de roles
        user = self.db.query(User).options(joinedload(User.roles)).filter(User.email == email).first()
        if user:
            # Cargar los roles asociados al usuario
            roles = [RoleInfo(id=role.id, nombre=role.nombre) for role in user.roles]
            return UserInDB(
                id=user.id,
                nombre=user.nombre,
                apellido=user.apellido,
                email=user.email,
                password=user.password,
                failed_attempts=user.failed_attempts,
                locked_until=user.locked_until,
                state_id=user.state_id,
                roles=roles
            )
        return None
    
    def get_roles_by_user(self, user_id: int):
        try:
            user = self.db.query(User).get(user_id)
            if user is None:
                return []
            return [RoleInfo(id=role.id, nombre=role.nombre) for role in user.roles]
        except Exception as e:
            # Manejar el error
            print(f"Error: {str(e)}")
            return []

    def update_user(self, user: UserInDB) -> UserInDB:
        user = self.db.query(User).get(user.id)
        if user:
            user.nombre = user.nombre
            user.apellido = user.apellido
            user.email = user.email
            user.password = user.password
            user.failed_attempts = user.failed_attempts
            user.locked_until = user.locked_until
            user.state_id = user.state_id
            
            self.db.commit()
            self.db.refresh(user)
            return self.get_user_by_email(user.email)
        return None
    
    def create_user(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def block_user(self, user_id: int, lock_duration: timedelta):
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.locked_until = datetime.now(timezone.utc) + lock_duration
            user.state_id = 3  # Estado bloqueado
            self.db.commit()
            return True
        return False
    
    def unblock_user(self, user_id: int):
        user = self.db.query(User).filter(User.id == user_id).first()
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

    # Métodos relacionados con la recuperación de contraseña
    def delete_password_recovery(self, user_id: int):
        self.db.query(RecuperacionContrasena).filter(RecuperacionContrasena.usuario_id == user_id).delete()
    
    def add_password_recovery(self, recovery: RecuperacionContrasena):
        self.db.add(recovery)
        self.db.commit()
    
    def get_password_recovery(self, user_id: int):
        return self.db.query(RecuperacionContrasena).filter(
            RecuperacionContrasena.usuario_id == user_id,
            RecuperacionContrasena.expiracion > datetime.utcnow()
        ).first()
        
    def get_password_recovery_with_pin(self, user_id: int, pin_hash: str):
        # Llamamos al método base para obtener la recuperación activa
        recovery = self.get_password_recovery(user_id)
        if recovery and recovery.pin == pin_hash:
            return recovery
        return None

    def delete_recovery(self, recovery: RecuperacionContrasena):
        self.db.delete(recovery)
        self.db.commit()

    # Métodos relacionados con la verificación en dos pasos
    def delete_two_factor_verification(self, user_id: int):
        self.db.query(VerificacionDospasos).filter(VerificacionDospasos.usuario_id == user_id).delete()
    
    def add_two_factor_verification(self, verification: VerificacionDospasos):
        self.db.add(verification)
        self.db.commit()
    
    def get_two_factor_verification(self, user_id: int, pin_hash: str):
        return self.db.query(VerificacionDospasos).filter(
            VerificacionDospasos.usuario_id == user_id,
            VerificacionDospasos.pin == pin_hash,
            VerificacionDospasos.expiracion > datetime.utcnow()
        ).first()

    def delete_two_factor_verification_entry(self, verification: VerificacionDospasos):
        self.db.delete(verification)
        self.db.commit()

    # Métodos relacionados con la confirmación de usuario
    def delete_user_confirmation(self, user_id: int):
        self.db.query(ConfirmacionUsuario).filter(ConfirmacionUsuario.usuario_id == user_id).delete()

    def add_user_confirmation(self, confirmation: ConfirmacionUsuario):
        self.db.add(confirmation)
        self.db.commit()
    
    def get_user_confirmation(self, user_id: int, pin_hash: str):
        return self.db.query(ConfirmacionUsuario).filter(
            ConfirmacionUsuario.usuario_id == user_id,
            ConfirmacionUsuario.pin == pin_hash,
            ConfirmacionUsuario.expiracion > datetime.utcnow()
        ).first()

    def delete_confirmation(self, confirmation: ConfirmacionUsuario):
        self.db.delete(confirmation)
        self.db.commit()
    
    def increase_confirmation_attempts(self, confirmation: ConfirmacionUsuario):
        confirmation.intentos += 1
        self.db.commit()
    
    def delete_user(self, user: User):
        self.db.delete(user)
        self.db.commit()
