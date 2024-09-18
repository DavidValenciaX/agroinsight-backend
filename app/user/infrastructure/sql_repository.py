from sqlalchemy.orm import Session, joinedload
from app.user.domain.schemas import UserCreate, UserInDB, Confirmation, TwoFactorAuth, PasswordRecovery
from app.user.infrastructure.orm_models import User, EstadoUsuario, Role, UserRole, RecuperacionContrasena, VerificacionDospasos, ConfirmacionUsuario
from app.user.infrastructure.orm_models import BlacklistedToken
from datetime import datetime, timezone, timedelta
from typing import Optional

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    # Métodos relacionados con el usuario
    def create_user(self, user: UserCreate) -> Optional[User]:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        user = self.db.query(User).options(joinedload(User.roles)).get(user_id)
        return user
    
    def get_all_users(self):
        return self.db.query(User).options(joinedload(User.roles), joinedload(User.estado)).all()

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
    
    def update_user_info(self, user: User, user_data: dict):
        """Actualiza la información del usuario con los datos proporcionados"""
        if 'nombre' in user_data and user_data['nombre']:
            user.nombre = user_data['nombre']
        if 'apellido' in user_data and user_data['apellido']:
            user.apellido = user_data['apellido']
        if 'email' in user_data and user_data['email']:
            user.email = user_data['email']
        
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            print(f"Error al actualizar el usuario: {e}")
            return None
        
    def update_user_info_by_admin(self, user: User, user_data: dict):
        """Actualiza la información del usuario con los datos proporcionados por un administrador."""
        if 'nombre' in user_data and user_data['nombre']:
            user.nombre = user_data['nombre']
        if 'apellido' in user_data and user_data['apellido']:
            user.apellido = user_data['apellido']
        if 'email' in user_data and user_data['email']:
            user.email = user_data['email']

        # Cambiar el estado del usuario basado en el estado_id
        if 'estado_id' in user_data and user_data['estado_id']:
            estado = self.db.query(EstadoUsuario).filter(EstadoUsuario.id == user_data['estado_id']).first()
            if estado:
                user.state_id = estado.id
            else:
                raise ValueError("Estado no válido")

        # Cambiar el rol del usuario basado en el rol_id
        if 'rol_id' in user_data and user_data['rol_id']:
            nuevo_rol = self.db.query(Role).filter(Role.id == user_data['rol_id']).first()
            if nuevo_rol:
                # Eliminar el rol actual y asignar el nuevo rol
                self.db.query(UserRole).filter(UserRole.usuario_id == user.id).delete()
                user_role = UserRole(usuario_id=user.id, rol_id=nuevo_rol.id)
                self.db.add(user_role)
            else:
                raise ValueError("Rol no válido")

        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            print(f"Error al actualizar el usuario por admin: {e}")
            return None
    
    def delete_user(self, user: UserInDB):
        try:
            self.db.delete(user)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al eliminar el usuario: {str(e)}")
            return False
    
    def block_user(self, user_id: int, lock_duration: timedelta):
        user = self.get_user_by_id(user_id)
        if user:
            user.locked_until = datetime.now(timezone.utc) + lock_duration
            user.state_id = self.get_locked_user_state_id()  # Estado bloqueado
            self.db.commit()
            return True
        return False
    
    # Métodos relacionados con la confirmación de usuario
    def delete_user_confirmations(self, user_id: int):
        self.db.query(ConfirmacionUsuario).filter(ConfirmacionUsuario.usuario_id == user_id).delete()
        self.db.commit()

    def add_user_confirmation(self, confirmation: Confirmation):
        self.db.add(confirmation)
        self.db.commit()
        
    def get_user_pending_confirmation(self, user_id: int):
        return self.db.query(ConfirmacionUsuario).filter(
        ConfirmacionUsuario.usuario_id == user_id
        ).first()
    
    def get_user_confirmation(self, user_id: int, pin_hash: str):
        return self.db.query(ConfirmacionUsuario).filter(
            ConfirmacionUsuario.usuario_id == user_id,
            ConfirmacionUsuario.pin == pin_hash,
            ConfirmacionUsuario.expiracion > datetime.now(timezone.utc)
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
            ConfirmacionUsuario.expiracion > datetime.now(timezone.utc)
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
            RecuperacionContrasena.expiracion > datetime.now(timezone.utc)
        ).first()

    def delete_recovery(self, recovery: PasswordRecovery):
        self.db.delete(recovery)
        self.db.commit()
        
    # Métodos relacionados con la lista negra de tokens
    def blacklist_token(self, token: str, user_id: int) -> bool:
        try:
            # Crear una nueva instancia del token blacklisteado, ahora con usuario_id
            blacklisted = BlacklistedToken(token=token, usuario_id=user_id)
            self.db.add(blacklisted)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al blacklistear el token: {e}")
            return False

    def is_token_blacklisted(self, token: str) -> bool:
        return self.db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first() is not None
        
    # Métodos relacionados con estados y roles
    def get_state_by_id(self, state_id: int):
        return self.db.query(EstadoUsuario).filter(EstadoUsuario.id == state_id).first()
    
    def get_role_by_id(self, role_id: int) -> Optional[Role]:
        return self.db.query(Role).filter(Role.id == role_id).first()
        
    def get_active_user_state_id(self) -> Optional[int]:
        active_state = self.db.query(EstadoUsuario).filter(EstadoUsuario.nombre == "active").first()
        return active_state.id if active_state else None

    def get_locked_user_state_id(self) -> Optional[int]:
        locked_state = self.db.query(EstadoUsuario).filter(EstadoUsuario.nombre == "locked").first()
        return locked_state.id if locked_state else None
    
    def get_pending_user_state_id(self) -> Optional[int]:
        locked_state = self.db.query(EstadoUsuario).filter(EstadoUsuario.nombre == "pending").first()
        return locked_state.id if locked_state else None
    
    def get_inactive_user_state_id(self) -> Optional[int]:
        """
        Retorna el ID del estado 'inactive' para los usuarios.
        """
        inactive_state = self.db.query(EstadoUsuario).filter(EstadoUsuario.nombre == "inactive").first()
        return inactive_state.id if inactive_state else None
    
    def get_admin_roles(self):
        """
        Obtiene los roles de 'Superusuario' y 'Administrador de finca'.
        """
        admin_roles = self.db.query(Role).filter(Role.nombre.in_(["Superusuario", "Administrador de finca"])).all()
        return admin_roles

    def deactivate_user(self, user_id: int) -> bool:
        """
        Cambia el estado del usuario a 'inactive'.
        """
        user = self.get_user_by_id(user_id)
        if user:
            inactive_state_id = self.get_inactive_user_state_id()
            if not inactive_state_id:
                print("No se encontró el estado 'inactive'.")
                return False

            user.state_id = inactive_state_id
            try:
                self.db.commit()
                return True
            except Exception as e:
                self.db.rollback()
                print(f"Error al actualizar el estado del usuario: {e}")
                return False
        return False

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