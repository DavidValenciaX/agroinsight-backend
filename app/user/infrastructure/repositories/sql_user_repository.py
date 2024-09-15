from sqlalchemy.orm import Session, joinedload
from app.user.domain.user_entities import UserCreate, UserInDB, RoleInfo, Confirmation, TwoFactorAuth, PasswordRecovery
from app.user.infrastructure.orm_models.user_orm_model import User
from app.user.infrastructure.orm_models.user_state_orm_model import EstadoUsuario
from app.user.infrastructure.orm_models.role_orm_model import Role
from app.user.infrastructure.orm_models.user_role_orm_model import UserRole
from app.user.infrastructure.orm_models.password_recovery_orm_model import RecuperacionContrasena
from app.user.infrastructure.orm_models.two_factor_verify_orm_model import VerificacionDospasos
from app.user.infrastructure.orm_models.user_confirmation_orm_model import ConfirmacionUsuario
from datetime import datetime, timezone, timedelta
from typing import Optional

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    # Métodos relacionados con el usuario
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        user = self.db.query(User).options(joinedload(User.roles)).get(user_id)
        return user

    def update_user(self, user: User) -> Optional[User]:
        user_in_db = self.db.query(User).get(user.id)  # Cargar el usuario desde la base de datos
        if user_in_db:
            # Actualizar los campos del usuario en la base de datos con los valores del user proporcionado
            user_in_db.nombre = user.nombre
            user_in_db.apellido = user.apellido
            user_in_db.email = user.email
            user_in_db.password = user.password
            user_in_db.failed_attempts = user.failed_attempts
            user_in_db.locked_until = user.locked_until
            user_in_db.state_id = user.state_id

            # Confirmar los cambios en la base de datos
            try:
                self.db.commit()
                self.db.refresh(user_in_db)  # Refrescar para obtener los datos actualizados
                return user_in_db  # Devolver el usuario actualizado como modelo ORM
            except Exception as e:
                self.db.rollback()
                print(f"Error al hacer commit: {e}")
                return None
        return None
    
    def create_user(self, user: UserCreate) -> Optional[User]:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete_user(self, user: UserInDB):
        """Elimina una instancia gestionada de User."""
        try:
            self.db.delete(user)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al eliminar el usuario: {str(e)}")
            return False
    
    def block_user(self, user_id: int, lock_duration: timedelta):
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.locked_until = datetime.now(timezone.utc) + lock_duration
            user.state_id = 3  # Estado bloqueado
            self.db.commit()
            return True
        return False
    
    # Métodos relacionados con estados y roles
    def get_state_by_id(self, state_id: int):
        return self.db.query(EstadoUsuario).filter(EstadoUsuario.id == state_id).first()
    
    def get_active_user_state(self):
        return self.db.query(EstadoUsuario).filter(EstadoUsuario.nombre == "active").first()

    def get_pending_user_state(self):
        return self.db.query(EstadoUsuario).filter(EstadoUsuario.nombre == "pending").first()

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
        self.db.commit()
    
    def add_password_recovery(self, recovery: PasswordRecovery):
        self.db.add(recovery)
        self.db.commit()
    
    def get_password_recovery(self, user_id: int):
        return self.db.query(RecuperacionContrasena).filter(
            RecuperacionContrasena.usuario_id == user_id,
            RecuperacionContrasena.expiracion > datetime.utcnow()
        ).first()

    def delete_recovery(self, recovery: PasswordRecovery):
        self.db.delete(recovery)
        self.db.commit()

    # Métodos relacionados con la verificación en dos pasos        
    def delete_two_factor_verification(self, user_id: int):
        deleted = self.db.query(VerificacionDospasos).filter(VerificacionDospasos.usuario_id == user_id).delete()
        self.db.commit()
        return deleted
    
    def add_two_factor_verification(self, verification: TwoFactorAuth):
        self.db.add(verification)
        self.db.commit()
    
    def get_two_factor_verification(self, user_id: int, pin_hash: str):
        return self.db.query(VerificacionDospasos).filter(
            VerificacionDospasos.usuario_id == user_id,
            VerificacionDospasos.pin == pin_hash,
            VerificacionDospasos.expiracion > datetime.now(timezone.utc)  # timezone-aware
        ).first()
        
    def increment_two_factor_attempts(self, user_id: int):
        accessTokenExpireMinutes = 10
        verification = self.db.query(VerificacionDospasos).filter(VerificacionDospasos.usuario_id == user_id).first()
        if verification:
            verification.intentos += 1
            current_intentos = verification.intentos  # Almacenar antes de posibles cambios
            if current_intentos >= 3:
                # Bloquear el usuario
                self.block_user(user_id, timedelta(minutes=accessTokenExpireMinutes))
                # Eliminar la verificación
                self.delete_two_factor_verification(user_id)
            self.db.commit()
            return current_intentos  # Devolver el valor almacenado
        return 0

    # Métodos relacionados con la confirmación de usuario
    def delete_user_confirmations(self, user_id: int):
        self.db.query(ConfirmacionUsuario).filter(ConfirmacionUsuario.usuario_id == user_id).delete()
        self.db.commit()

    def add_user_confirmation(self, confirmation: Confirmation):
        self.db.add(confirmation)
        self.db.commit()
    
    def get_user_confirmation(self, user_id: int, pin_hash: str):
        return self.db.query(ConfirmacionUsuario).filter(
            ConfirmacionUsuario.usuario_id == user_id,
            ConfirmacionUsuario.pin == pin_hash,
            ConfirmacionUsuario.expiracion > datetime.utcnow()
        ).first()

    def increment_confirmation_attempts(self, user_id: int):
        confirmation = self.get_active_confirmation(user_id)
        if confirmation:
            confirmation.intentos += 1
            self.db.commit()
            return confirmation.intentos
        return 0

    def get_active_confirmation(self, user_id: int):
        return self.db.query(ConfirmacionUsuario).filter(
            ConfirmacionUsuario.usuario_id == user_id,
            ConfirmacionUsuario.expiracion > datetime.utcnow()
        ).first()

    def update_user_state(self, user_id: int, new_state_id: int):
        user = self.get_user_by_id(user_id)
        if user:
            user.state_id = new_state_id
            try:
                self.db.commit()
                self.db.refresh(user)  # Refresca el objeto para asegurar que los cambios se han aplicado
                return True
            except Exception as e:
                self.db.rollback()
                print(f"Error al hacer commit: {e}")
                return False
        return False