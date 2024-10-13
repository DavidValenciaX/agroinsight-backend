from sqlalchemy.orm import Session, joinedload
from app.farm.infrastructure.orm_models import Farm
from app.infrastructure.common.common_exceptions import DomainException
from app.infrastructure.common.datetime_utils import datetime_timezone_utc_now
from app.user.infrastructure.orm_models import (
    User, UserState, Role, UserFarmRole, PasswordRecovery,
    TwoStepVerification, UserConfirmation, BlacklistedToken
)
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import status

# Constantes para roles
ADMIN_ROLE_NAME = "Administrador de Finca"
WORKER_ROLE_NAME = "Trabajador agrícola"
UNCONFIRMED_ROLE_NAME = "Rol no confirmado"
UNASSIGNED_ROLE_NAME = "Rol no asignado"

# Constantes para estados
ACTIVE_STATE_NAME = "active"
LOCKED_STATE_NAME = "locked"
PENDING_STATE_NAME = "pending"
INACTIVE_STATE_NAME = "inactive"

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
        return self.db.query(User).get(user_id)
    
    def get_all_users(self) -> List[User]:
        return self.db.query(User).options(joinedload(User.estado)).all()
    
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
        return self.db.query(UserConfirmation).filter(
            UserConfirmation.usuario_id == user_id
        ).order_by(UserConfirmation.created_at.desc()).first()

    def get_last_two_factor_verification(self, user_id: int):
        return self.db.query(TwoStepVerification).filter(
            TwoStepVerification.usuario_id == user_id
        ).order_by(TwoStepVerification.created_at.desc()).first()

    def get_last_password_recovery(self, user_id: int):
        return self.db.query(PasswordRecovery).filter(
            PasswordRecovery.usuario_id == user_id
        ).order_by(PasswordRecovery.created_at.desc()).first()
    
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
            
        print(user_data['finca_id'])

        # Cambiar el estado del usuario basado en el estado_id
        if 'estado_id' in user_data and user_data['estado_id']:
            estado = self.get_state_by_id(user_data['estado_id'])
            if not estado:
                raise ValueError("Estado no válido")
            
            user.state_id = estado.id

        # Cambiar el rol del usuario basado en el rol_id, asegurando que esté asociado a la finca
        if 'rol_id' in user_data and user_data['rol_id']:
            nuevo_rol = self.get_role_by_id(user_data['rol_id'])
            if not nuevo_rol:
                raise ValueError("Rol no válido")
        
        if 'finca_id' in user_data and user_data['finca_id']:
            farm = self.db.query(Farm).filter(Farm.id == user_data['finca_id']).first()
            if not farm:
                raise ValueError("Finca no válida")
            
        # Verificar si el usuario tiene el rol de trabajador asociado a la finca especificada
        user_finca_rol = (
            self.db.query(UserFarmRole)
            .filter(UserFarmRole.usuario_id == user.id)
            .filter(UserFarmRole.finca_id == farm.id)
            .filter(UserFarmRole.rol_id == nuevo_rol.id)
            .first()
            )
            
        if not user_finca_rol:
            # Eliminar el rol actual y asignar el nuevo rol asociado a la finca
            self.db.query(UserFarmRole).filter(UserFarmRole.usuario_id == user.id, UserFarmRole.finca_id == farm.id).delete()
            user_role = UserFarmRole(usuario_id=user.id, finca_id=farm.id, rol_id=nuevo_rol.id)
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
            user.locked_until = datetime_timezone_utc_now() + lock_duration
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
            deleted = self.db.query(UserConfirmation).filter(UserConfirmation.usuario_id == user_id).delete()
            self.db.commit()
            return deleted
        except Exception as e:
            self.db.rollback()
            print(f"Error al eliminar confirmaciones del usuario: {e}")
            return 0

    def add_user_confirmation(self, confirmation: UserConfirmation) -> bool:
        try:
            self.db.add(confirmation)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al agregar la confirmación del usuario: {e}")
            return False

    def update_user_confirmation(self, confirmation: UserConfirmation) -> bool:
        try:
            self.db.commit()
            self.db.refresh(confirmation)
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al actualizar la confirmación del usuario: {e}")
            return False
        
    def get_user_pending_confirmation(self, user_id: int) -> Optional[UserConfirmation]:
        """Verifica si el usuario tiene una confirmación pendiente."""
        
        # Primero obtiene el registro de UserConfirmation para el user_id dado
        user_confirmation = self.db.query(UserConfirmation).filter(
            UserConfirmation.usuario_id == user_id
        ).first()

        # Si no se encuentra el registro, imprime un mensaje apropiado para depurar y retorna None
        if not user_confirmation:
            print("No se encontró ninguna confirmación para este usuario.")
            return None

        # Ahora que tienes el objeto, puedes imprimir el valor de expiracion real
        print("Fecha de expiración en BD:", user_confirmation.expiracion)
        print("Fecha actual:", datetime_timezone_utc_now())

        # Realiza la verificación para confirmar si la confirmación sigue pendiente
        if user_confirmation.expiracion > datetime_timezone_utc_now():
            return user_confirmation
        else:
            print("La confirmación ha expirado.")
        
        return self.db.query(UserConfirmation).filter(
            UserConfirmation.usuario_id == user_id,
            UserConfirmation.expiracion > datetime_timezone_utc_now()
        ).first()

    def get_user_confirmation(self, user_id: int, pin_hash: str) -> Optional[UserConfirmation]:
        return self.db.query(UserConfirmation).filter(
            UserConfirmation.usuario_id == user_id,
            UserConfirmation.pin == pin_hash,
            UserConfirmation.expiracion > datetime_timezone_utc_now()
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
            deleted = self.db.query(TwoStepVerification).filter(TwoStepVerification.usuario_id == user_id).delete()
            self.db.commit()
            return deleted
        except Exception as e:
            self.db.rollback()
            print(f"Error al eliminar la verificación de dos pasos: {e}")
            return 0

    def add_two_factor_verification(self, verification: TwoStepVerification) -> bool:
        try:
            self.db.add(verification)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al agregar la verificación de dos pasos: {e}")
            return False
        
    def update_two_factor_verification(self, verification: TwoStepVerification) -> bool:
        try:
            self.db.commit()
            self.db.refresh(verification)
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al actualizar la verificacion en dos pasos: {e}")
            return False
    
    def get_user_pending_2fa_verification(self, user_id: int) -> Optional[TwoStepVerification]:
        """Verifica si el usuario tiene una verificacion 2fa pendiente."""
        return self.db.query(TwoStepVerification).filter(
            TwoStepVerification.usuario_id == user_id,
            TwoStepVerification.expiracion > datetime_timezone_utc_now()
        ).first()
    
    def get_two_factor_verification(self, user_id: int, pin_hash: str) -> Optional[TwoStepVerification]:
        return self.db.query(TwoStepVerification).filter(
            TwoStepVerification.usuario_id == user_id,
            TwoStepVerification.pin == pin_hash,
            TwoStepVerification.expiracion > datetime_timezone_utc_now()
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
            deleted = self.db.query(PasswordRecovery).filter(PasswordRecovery.usuario_id == user_id).delete()
            self.db.commit()
            return deleted
        except Exception as e:
            self.db.rollback()
            print(f"Error al eliminar la recuperación de contraseña: {e}")
            return 0

    def add_password_recovery(self, recovery: PasswordRecovery) -> bool:
        try:
            self.db.add(recovery)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al agregar la recuperación de contraseña: {e}")
            return False
        
    def update_password_recovery(self, recovery: PasswordRecovery) -> bool:
        try:
            self.db.commit()
            self.db.refresh(recovery)
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al actualizar la recuperación de contraseña: {e}")
            return False

    def get_password_recovery(self, user_id: int) -> Optional[PasswordRecovery]:
        return self.db.query(PasswordRecovery).filter(
            PasswordRecovery.usuario_id == user_id,
            PasswordRecovery.expiracion > datetime_timezone_utc_now()
        ).first()

    def delete_recovery(self, recovery: PasswordRecovery) -> bool:
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
    def get_state_by_id(self, state_id: int) -> Optional[UserState]:
        return self.db.query(UserState).filter(UserState.id == state_id).first()

    def get_role_by_id(self, role_id: int) -> Optional[Role]:
        return self.db.query(Role).filter(Role.id == role_id).first()

    def get_active_user_state_id(self) -> Optional[int]:
        active_state = self.db.query(UserState).filter(UserState.nombre == ACTIVE_STATE_NAME).first()
        return active_state.id if active_state else None

    def get_locked_user_state_id(self) -> Optional[int]:
        locked_state = self.db.query(UserState).filter(UserState.nombre == LOCKED_STATE_NAME).first()
        return locked_state.id if locked_state else None

    def get_pending_user_state_id(self) -> Optional[int]:
        pending_state = self.db.query(UserState).filter(UserState.nombre == PENDING_STATE_NAME).first()
        return pending_state.id if pending_state else None

    def get_inactive_user_state_id(self) -> Optional[int]:
        inactive_state = self.db.query(UserState).filter(UserState.nombre == INACTIVE_STATE_NAME).first()
        return inactive_state.id if inactive_state else None

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
        return self.db.query(Role).filter(Role.nombre == UNCONFIRMED_ROLE_NAME).first()
    
    def get_registered_user_role(self) -> Optional[Role]:
        return self.db.query(Role).filter(Role.nombre == UNASSIGNED_ROLE_NAME).first()

    def assign_role_to_user(self, user_id: int, role_id: int, farm_id: int = None) -> bool:
        try:
            user_farm_role = UserFarmRole(usuario_id=user_id, rol_id=role_id, finca_id=farm_id)
            self.db.add(user_farm_role)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al asignar rol al usuario: {e}")
            return False

    def change_user_role(self, user_id: int, old_role: Role, new_role: Role, farm_id: int = None) -> bool:
        user_farm_role = self.db.query(UserFarmRole).filter(
            UserFarmRole.usuario_id == user_id,
            UserFarmRole.rol_id == old_role.id,
            UserFarmRole.finca_id == farm_id
        ).first()

        if user_farm_role:
            user_farm_role.rol_id = new_role.id
            try:
                self.db.commit()
                self.db.refresh(user_farm_role)
                return True
            except Exception as e:
                self.db.rollback()
                print(f"Error al cambiar el rol del usuario: {e}")
                return False

        return False

    # Métodos auxiliares
    
    def get_role_by_name(self, role_name: str) -> Optional[Role]:
        return self.db.query(Role).filter(Role.nombre == role_name).first()
    
    def get_admin_role(self):
        try:
            return self.get_role_by_name(ADMIN_ROLE_NAME)
        except Exception as e:
            raise DomainException(message = f"Error al obtener el rol de administrador: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_worker_role(self):
        try:
            return self.get_role_by_name(WORKER_ROLE_NAME)
        except Exception as e:
            raise DomainException(message = f"Error al obtener el rol de trabajador: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_user_roles_fincas(self, user_id: int, finca_id: int) -> List[Role]:
        return self.db.query(Role).join(UserFarmRole).filter(
            UserFarmRole.usuario_id == user_id,
            UserFarmRole.finca_id == finca_id
        ).all()
        
    def user_exists(self, user_id: int) -> bool:
        return self.db.query(User).filter(User.id == user_id).first() is not None

    def delete_expired_confirmations_and_users(self) -> int:
        """
        Elimina las confirmaciones de usuario expiradas y los usuarios asociados.

        Returns:
            int: El número de confirmaciones eliminadas.
        """
        try:
            # Obtener las confirmaciones expiradas
            expired_confirmations = self.db.query(UserConfirmation).filter(
                UserConfirmation.expiracion < datetime_timezone_utc_now()
            ).all()

            # Eliminar usuarios asociados a las confirmaciones expiradas
            for confirmation in expired_confirmations:
                user = self.get_user_by_id(confirmation.usuario_id)
                if user:
                    self.db.delete(user)

            # Eliminar confirmaciones expiradas
            deleted_count = self.db.query(UserConfirmation).filter(
                UserConfirmation.expiracion < datetime_timezone_utc_now()
            ).delete(synchronize_session=False)

            self.db.commit()
            return deleted_count
        except Exception as e:
            self.db.rollback()
            print(f"Error al eliminar confirmaciones expiradas y usuarios: {e}")
            return 0

    def get_expired_confirmation(self, user_id: int) -> Optional[UserConfirmation]:
        """
        Obtiene la confirmación expirada de un usuario específico.

        Returns:
            UserConfirmation: La confirmación expirada si existe, de lo contrario None.
        """
        return self.db.query(UserConfirmation).filter(
            UserConfirmation.usuario_id == user_id,
            UserConfirmation.expiracion < datetime_timezone_utc_now()
        ).first()
        
    def delete_expired_confirmation(self, user_id: int) -> int: 
        try:
            deleted_count = self.db.query(UserConfirmation).filter(
                UserConfirmation.usuario_id == user_id,         
                UserConfirmation.expiracion < datetime_timezone_utc_now()
            ).delete(synchronize_session=False)
            self.db.commit()
            return deleted_count
        except Exception as e:
            self.db.rollback()
            print(f"Error al eliminar confirmaciones expiradas: {e}")
            return 0

    def delete_expired_two_factor_verifications(self, user_id: int) -> int:
        """
        Elimina las verificaciones de dos pasos expiradas de un usuario específico.

        Returns:
            int: El número de verificaciones eliminadas.
        """
        try:
            deleted_count = self.db.query(TwoStepVerification).filter(
                TwoStepVerification.usuario_id == user_id,
                TwoStepVerification.expiracion < datetime_timezone_utc_now()
            ).delete(synchronize_session=False)

            self.db.commit()
            return deleted_count
        except Exception as e:
            self.db.rollback()
            print(f"Error al eliminar verificaciones de dos pasos expiradas: {e}")
            return 0