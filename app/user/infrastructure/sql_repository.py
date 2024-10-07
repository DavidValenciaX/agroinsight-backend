from sqlalchemy.orm import Session, joinedload
from app.user.infrastructure.orm_models import (
    User, EstadoUsuario, Role, UserRole, RecuperacionContrasena,
    VerificacionDospasos, ConfirmacionUsuario, BlacklistedToken
)
from datetime import datetime, timezone, timedelta
from typing import Optional, List

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    # Métodos relacionados con el usuario
    def create_user(self, user: User) -> Optional[User]:
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear el usuario: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).options(joinedload(User.roles)).get(user_id)
    
    def get_all_users(self) -> List[User]:
            return self.db.query(User).options(joinedload(User.roles), joinedload(User.estado)).all()
    
    def update_user(self, user: User) -> Optional[User]:
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            print(f"Error al actualizar el usuario: {e}")
            return None
        
    def get_last_user_confirmation(self, user_id: int):
        return self.db.query(ConfirmacionUsuario).filter(
            ConfirmacionUsuario.usuario_id == user_id
        ).order_by(ConfirmacionUsuario.created_at.desc()).first()

    def get_last_two_factor_verification(self, user_id: int):
        return self.db.query(VerificacionDospasos).filter(
            VerificacionDospasos.usuario_id == user_id
        ).order_by(VerificacionDospasos.created_at.desc()).first()

    def get_last_password_recovery(self, user_id: int):
        return self.db.query(RecuperacionContrasena).filter(
            RecuperacionContrasena.usuario_id == user_id
        ).order_by(RecuperacionContrasena.created_at.desc()).first()
    
    def update_user_info(self, user: User, user_data: dict) -> Optional[User]:
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
        
    def update_user_info_by_admin(self, user: User, user_data: dict) -> Optional[User]:
        """Actualiza la información del usuario con los datos proporcionados por un administrador."""
        if 'nombre' in user_data and user_data['nombre']:
            user.nombre = user_data['nombre']
        if 'apellido' in user_data and user_data['apellido']:
            user.apellido = user_data['apellido']
        if 'email' in user_data and user_data['email']:
            user.email = user_data['email']

        # Cambiar el estado del usuario basado en el estado_id
        if 'estado_id' in user_data and user_data['estado_id']:
            estado = self.get_state_by_id(user_data['estado_id'])
            if not estado:
                raise ValueError("Estado no válido")
            
            user.state_id = estado.id

        # Cambiar el rol del usuario basado en el rol_id
        if 'rol_id' in user_data and user_data['rol_id']:
            nuevo_rol = self.get_role_by_id(user_data['rol_id'])
            if not nuevo_rol:
                raise ValueError("Rol no válido")
            
            # Eliminar el rol actual y asignar el nuevo rol
            self.db.query(UserRole).filter(UserRole.usuario_id == user.id).delete()
            user_role = UserRole(usuario_id=user.id, rol_id=nuevo_rol.id)
            self.db.add(user_role)

        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            print(f"Error al actualizar el usuario por admin: {e}")
            return None
    
    def delete_user(self, user: User) -> bool:
        try:
            self.db.delete(user)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al eliminar el usuario: {str(e)}")
            return False
    
    def block_user(self, user_id: int, lock_duration: timedelta) -> bool:
        user = self.get_user_by_id(user_id)
        if user:
            user.locked_until = datetime.now(timezone.utc) + lock_duration
            user.state_id = self.get_locked_user_state_id()  # Estado bloqueado
            try:
                self.db.commit()
                self.db.refresh(user)
                return True
            except Exception as e:
                self.db.rollback()
                print(f"Error al bloquear el usuario: {e}")
                return False
        return False
    
    # Métodos relacionados con la confirmación de usuario
    def delete_user_confirmations(self, user_id: int) -> int:
        try:
            deleted = self.db.query(ConfirmacionUsuario).filter(ConfirmacionUsuario.usuario_id == user_id).delete()
            self.db.commit()
            return deleted
        except Exception as e:
            self.db.rollback()
            print(f"Error al eliminar confirmaciones del usuario: {e}")
            return 0

    def add_user_confirmation(self, confirmation: ConfirmacionUsuario) -> bool:
        try:
            self.db.add(confirmation)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al agregar la confirmación del usuario: {e}")
            return False

    def update_user_confirmation(self, confirmation: ConfirmacionUsuario) -> bool:
        try:
            self.db.commit()
            self.db.refresh(confirmation)
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al actualizar la confirmación del usuario: {e}")
            return False
        
    def get_user_pending_confirmation(self, user_id: int) -> Optional[ConfirmacionUsuario]:
        """Verifica si el usuario tiene una confirmación pendiente."""
        return self.db.query(ConfirmacionUsuario).filter(
            ConfirmacionUsuario.usuario_id == user_id,
            ConfirmacionUsuario.expiracion > datetime.now(timezone.utc)
        ).first()

    def get_user_confirmation(self, user_id: int, pin_hash: str) -> Optional[ConfirmacionUsuario]:
        return self.db.query(ConfirmacionUsuario).filter(
            ConfirmacionUsuario.usuario_id == user_id,
            ConfirmacionUsuario.pin == pin_hash,
            ConfirmacionUsuario.expiracion > datetime.now(timezone.utc)
        ).first()

    def increment_confirmation_attempts(self, user_id: int) -> int:
        confirmation = self.get_user_pending_confirmation(user_id)
        if confirmation:
            confirmation.intentos += 1
            try:
                self.db.commit()
                return confirmation.intentos
            except Exception as e:
                self.db.rollback()
                print(f"Error al incrementar intentos de confirmación: {e}")
                return confirmation.intentos
        return 0

    def update_user_state(self, user_id: int, new_state_id: int) -> bool:
        user = self.get_user_by_id(user_id)
        if user:
            user.state_id = new_state_id
            try:
                self.db.commit()
                self.db.refresh(user)
                return True
            except Exception as e:
                self.db.rollback()
                print(f"Error al actualizar el estado del usuario: {e}")
                return False
        return False
    
    # Métodos relacionados con la verificación en dos pasos        
    def delete_two_factor_verification(self, user_id: int) -> int:
        try:
            deleted = self.db.query(VerificacionDospasos).filter(VerificacionDospasos.usuario_id == user_id).delete()
            self.db.commit()
            return deleted
        except Exception as e:
            self.db.rollback()
            print(f"Error al eliminar la verificación de dos pasos: {e}")
            return 0

    def add_two_factor_verification(self, verification: VerificacionDospasos) -> bool:
        try:
            self.db.add(verification)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al agregar la verificación de dos pasos: {e}")
            return False
        
    def update_two_factor_verification(self, verification: VerificacionDospasos) -> bool:
        try:
            self.db.commit()
            self.db.refresh(verification)
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al actualizar la verificacion en dos pasos: {e}")
            return False
    
    def get_user_pending_2fa_verification(self, user_id: int) -> Optional[VerificacionDospasos]:
        """Verifica si el usuario tiene una verificacion 2fa pendiente."""
        return self.db.query(VerificacionDospasos).filter(
            VerificacionDospasos.usuario_id == user_id,
            VerificacionDospasos.expiracion > datetime.now(timezone.utc)
        ).first()
    
    def get_two_factor_verification(self, user_id: int, pin_hash: str) -> Optional[VerificacionDospasos]:
        return self.db.query(VerificacionDospasos).filter(
            VerificacionDospasos.usuario_id == user_id,
            VerificacionDospasos.pin == pin_hash,
            VerificacionDospasos.expiracion > datetime.now(timezone.utc)
        ).first()
        
    def increment_two_factor_attempts(self, user_id: int) -> int:
        verification = self.get_user_pending_2fa_verification(user_id)
        if verification:
            verification.intentos += 1
            try:
                self.db.commit()
                return verification.intentos
            except Exception as e:
                self.db.rollback()
                print(f"Error al incrementar intentos de doble factor de autenticación: {e}")
                return verification.intentos
        return 0

    # Métodos relacionados con la recuperación de contraseña        
    def delete_password_recovery(self, user_id: int) -> int:
        try:
            deleted = self.db.query(RecuperacionContrasena).filter(RecuperacionContrasena.usuario_id == user_id).delete()
            self.db.commit()
            return deleted
        except Exception as e:
            self.db.rollback()
            print(f"Error al eliminar la recuperación de contraseña: {e}")
            return 0

    def add_password_recovery(self, recovery: RecuperacionContrasena) -> bool:
        try:
            self.db.add(recovery)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al agregar la recuperación de contraseña: {e}")
            return False
        
    def update_password_recovery(self, recovery: RecuperacionContrasena) -> bool:
        try:
            self.db.commit()
            self.db.refresh(recovery)
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al actualizar la recuperación de contraseña: {e}")
            return False

    def get_password_recovery(self, user_id: int) -> Optional[RecuperacionContrasena]:
        return self.db.query(RecuperacionContrasena).filter(
            RecuperacionContrasena.usuario_id == user_id,
            RecuperacionContrasena.expiracion > datetime.now(timezone.utc)
        ).first()

    def delete_recovery(self, recovery: RecuperacionContrasena) -> bool:
        try:
            self.db.delete(recovery)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al eliminar la recuperación: {e}")
            return False

    # Métodos relacionados con la lista negra de tokens
    def blacklist_token(self, token: str, user_id: int) -> bool:
        try:
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
    def get_state_by_id(self, state_id: int) -> Optional[EstadoUsuario]:
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
        pending_state = self.db.query(EstadoUsuario).filter(EstadoUsuario.nombre == "pending").first()
        return pending_state.id if pending_state else None

    def get_inactive_user_state_id(self) -> Optional[int]:
        inactive_state = self.db.query(EstadoUsuario).filter(EstadoUsuario.nombre == "inactive").first()
        return inactive_state.id if inactive_state else None

    def get_admin_roles(self) -> List[Role]:
        admin_roles = self.db.query(Role).filter(Role.nombre.in_(["Superusuario", "Administrador de Finca"])).all()
        return admin_roles

    def deactivate_user(self, user_id: int) -> bool:
        user = self.get_user_by_id(user_id)
        if user:
            inactive_state_id = self.get_inactive_user_state_id()
            if not inactive_state_id:
                print("No se encontró el estado 'inactive'.")
                return False

            user.state_id = inactive_state_id
            try:
                self.db.commit()
                self.db.refresh(user)
                return True
            except Exception as e:
                self.db.rollback()
                print(f"Error al actualizar el estado del usuario: {e}")
                return False
        return False

    def get_unconfirmed_user_role(self) -> Optional[Role]:
        return self.db.query(Role).filter(Role.nombre == "Usuario No Confirmado").first()
    
    def get_registered_user_role(self) -> Optional[Role]:
        return self.db.query(Role).filter(Role.nombre == "Usuario").first()

    def assign_role_to_user(self, user_id: int, role_id: int) -> bool:
        try:
            user_role = UserRole(usuario_id=user_id, rol_id=role_id)
            self.db.add(user_role)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al asignar rol al usuario: {e}")
            return False

    def change_user_role(self, user_id: int, old_role:Role, new_role:Role) -> bool:
        
        if old_role and new_role:
            user_role = self.db.query(UserRole).filter(
                UserRole.usuario_id == user_id,
                UserRole.rol_id == old_role.id
            ).first()

            if user_role:
                user_role.rol_id = new_role.id
                try:
                    self.db.commit()
                    self.db.refresh(user_role)
                    return True
                except Exception as e:
                    self.db.rollback()
                    print(f"Error al cambiar el rol del usuario: {e}")
                    return False

        return False

    # Métodos auxiliares
    def get_role_by_name(self, role_name: str) -> Optional[Role]:
        return self.db.query(Role).filter(Role.nombre == role_name).first()