from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from app.user.domain.schemas import UserCreate, UserInDB
from app.user.infrastructure.orm_models import (
    User, UserState, Role, PasswordRecovery,
    TwoStepVerification, UserConfirmation, BlacklistedToken
)
from typing import Optional, List

class UserRepository:
    """
    Repositorio para manejar operaciones relacionadas con usuarios en la base de datos.

    Esta clase proporciona métodos para realizar operaciones CRUD en usuarios y entidades relacionadas,
    como confirmaciones de usuario, verificación de dos pasos, recuperación de contraseña y tokens en lista negra.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy para realizar operaciones.
    """

    def __init__(self, db: Session):
        """
        Inicializa el repositorio de usuarios.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por su dirección de correo electrónico.

        Args:
            email (str): Dirección de correo electrónico del usuario.

        Returns:
            Optional[User]: El usuario si se encuentra, None en caso contrario.
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Obtiene un usuario por su ID.

        Args:
            user_id (int): ID del usuario.

        Returns:
            Optional[User]: El usuario si se encuentra, None en caso contrario.
        """
        return self.db.query(User).get(user_id)
    
    def get_user_with_confirmation(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario con su información de confirmación por correo electrónico.

        Args:
            email (str): Dirección de correo electrónico del usuario.

        Returns:
            Optional[User]: El usuario con información de confirmación si se encuentra, None en caso contrario.
        """
        return self.db.query(User).options(joinedload(User.confirmacion)).filter(User.email == email).first()
    
    def get_user_with_two_factor_verification(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario con su información de verificación de dos pasos por correo electrónico.

        Args:
            email (str): Dirección de correo electrónico del usuario.

        Returns:
            Optional[User]: El usuario con información de verificación de dos pasos si se encuentra, None en caso contrario.
        """
        return self.db.query(User).options(joinedload(User.verificacion_dos_pasos)).filter(User.email == email).first()
    
    def get_user_with_password_recovery(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario con su información de recuperación de contraseña por correo electrónico.

        Args:
            email (str): Dirección de correo electrónico del usuario.

        Returns:
            Optional[User]: El usuario con información de recuperación de contraseña si se encuentra, None en caso contrario.
        """
        return self.db.query(User).options(joinedload(User.recuperacion_contrasena)).filter(User.email == email).first()
    
    def get_all_users(self) -> List[User]:
        """
        Obtiene todos los usuarios con su información de estado.

        Returns:
            List[User]: Lista de todos los usuarios con su estado.
        """
        return self.db.query(User).options(joinedload(User.estado)).all()
    
    def add_user(self, user: UserCreate, state_id: int) -> Optional[User]:
        """
        Agrega un nuevo usuario a la base de datos.

        Args:
            user (User): Objeto de usuario a agregar.

        Returns:
            Optional[User]: El usuario agregado si tiene éxito, None en caso de error.
        """
        try:
            new_user = User(
                nombre=user.nombre,
                apellido=user.apellido,
                email=user.email,
                password=user.password,
                state_id=state_id
            )
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            return new_user
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear el usuario: {e}")
            return None
        
    def update_user(self, user: UserInDB) -> Optional[User]:
        """
        Actualiza un usuario existente en la base de datos.

        Args:
            user (User): Objeto de usuario con los datos actualizados.

        Returns:
            Optional[User]: El usuario actualizado si tiene éxito, None en caso de error.
        """
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            print(f"Error al actualizar el usuario: {e}")
            return None
        
    def delete_user(self, user: User) -> bool:
        """
        Elimina un usuario de la base de datos.

        Args:
            user (User): Objeto de usuario a eliminar.

        Returns:
            bool: True si se eliminó con éxito, False en caso de error.
        """
        try:
            self.db.delete(user)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al eliminar el usuario: {str(e)}")
            return False
    
    def add_user_confirmation(self, user_id: int, pin_hash: str, expiration_datetime: datetime, resends: int, created_at: datetime) -> bool:
        """
        Agrega una confirmación de usuario a la base de datos.

        Args:
            user_id (int): ID del usuario.
            pin_hash (str): Hash del PIN.
            expiration_datetime (datetime): Fecha y hora de expiración del PIN.
            resends (int): Número de reenvíos del PIN.
            created_at (datetime): Fecha y hora de creación del registro.

        Returns:
            bool: True si se agregó con éxito, False en caso de error.
        """
        try:
            confirmation = UserConfirmation(
                usuario_id=user_id,
                pin=pin_hash,
                expiracion=expiration_datetime,
                resends=resends,
                created_at=created_at
            )
            self.db.add(confirmation)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al agregar la confirmación del usuario: {e}")
            return False

    def update_user_confirmation(self, confirmation: UserConfirmation) -> bool:
        """
        Actualiza una confirmación de usuario existente en la base de datos.

        Args:
            confirmation (UserConfirmation): Objeto de confirmación de usuario con los datos actualizados.

        Returns:
            bool: True si se actualizó con éxito, False en caso de error.
        """
        try:
            self.db.commit()
            self.db.refresh(confirmation)
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al actualizar la confirmación del usuario: {e}")
            return False
        
    def delete_user_confirmation(self, confirmation: UserConfirmation) -> bool:
        """
        Elimina una confirmación de usuario de la base de datos.

        Args:
            confirmation (UserConfirmation): Objeto de confirmación de usuario a eliminar.

        Returns:
            bool: True si se eliminó con éxito, False en caso de error.
        """
        try:
            self.db.delete(confirmation)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al eliminar la confirmación del usuario: {e}")
            return False
    
    def add_two_factor_verification(self, verification: TwoStepVerification) -> bool:
        """
        Agrega una verificación de dos pasos a la base de datos.

        Args:
            verification (TwoStepVerification): Objeto de verificación de dos pasos a agregar.

        Returns:
            bool: True si se agregó con éxito, False en caso de error.
        """
        try:
            self.db.add(verification)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al agregar la verificación de dos pasos: {e}")
            return False
        
    def update_two_factor_verification(self, verification: TwoStepVerification) -> bool:
        """
        Actualiza una verificación de dos pasos existente en la base de datos.

        Args:
            verification (TwoStepVerification): Objeto de verificación de dos pasos con los datos actualizados.

        Returns:
            bool: True si se actualizó con éxito, False en caso de error.
        """
        try:
            self.db.commit()
            self.db.refresh(verification)
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al actualizar la verificacion en dos pasos: {e}")
            return False
        
    def delete_two_factor_verification(self, verification: TwoStepVerification) -> bool:
        """
        Elimina una verificación de dos pasos de la base de datos.

        Args:
            verification (TwoStepVerification): Objeto de verificación de dos pasos a eliminar.

        Returns:
            bool: True si se eliminó con éxito, False en caso de error.
        """
        try:
            self.db.delete(verification)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al eliminar la verificación de dos pasos: {e}")
            return False

    def add_password_recovery(self, recovery: PasswordRecovery) -> bool:
        """
        Agrega una recuperación de contraseña a la base de datos.

        Args:
            recovery (PasswordRecovery): Objeto de recuperación de contraseña a agregar.

        Returns:
            bool: True si se agregó con éxito, False en caso de error.
        """
        try:
            self.db.add(recovery)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al agregar la recuperación de contraseña: {e}")
            return False
        
    def update_password_recovery(self, recovery: PasswordRecovery) -> bool:
        """
        Actualiza una recuperación de contraseña existente en la base de datos.

        Args:
            recovery (PasswordRecovery): Objeto de recuperación de contraseña con los datos actualizados.

        Returns:
            bool: True si se actualizó con éxito, False en caso de error.
        """
        try:
            self.db.commit()
            self.db.refresh(recovery)
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al actualizar la recuperación de contraseña: {e}")
            return False

    def delete_password_recovery(self, recovery: PasswordRecovery) -> bool:
        """
        Elimina una recuperación de contraseña de la base de datos.

        Args:
            recovery (PasswordRecovery): Objeto de recuperación de contraseña a eliminar.

        Returns:
            bool: True si se eliminó con éxito, False en caso de error.
        """
        try:
            self.db.delete(recovery)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al eliminar la recuperación: {e}")
            return False

    def blacklist_token(self, blacklisted: BlacklistedToken) -> bool:
        """
        Agrega un token a la lista negra en la base de datos.

        Args:
            blacklisted (BlacklistedToken): Objeto de token en lista negra a agregar.

        Returns:
            bool: True si se agregó con éxito, False en caso de error.
        """
        try:
            self.db.add(blacklisted)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al blacklistear el token: {e}")
            return False

    def is_token_blacklisted(self, token: str) -> bool:
        """
        Verifica si un token está en la lista negra.

        Args:
            token (str): Token a verificar.

        Returns:
            bool: True si el token está en la lista negra, False en caso contrario.
        """
        return self.db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first() is not None

    def get_state_by_id(self, state_id: int) -> Optional[UserState]:
        """
        Obtiene un estado de usuario por su ID.

        Args:
            state_id (int): ID del estado de usuario.

        Returns:
            Optional[UserState]: El estado de usuario si se encuentra, None en caso contrario.
        """
        return self.db.query(UserState).filter(UserState.id == state_id).first()
    
    def get_state_by_name(self, state_name: str) -> Optional[UserState]:
        """
        Obtiene un estado de usuario por su nombre.

        Args:
            state_name (str): Nombre del estado de usuario.

        Returns:
            Optional[UserState]: El estado de usuario si se encuentra, None en caso contrario.
        """
        return self.db.query(UserState).filter(UserState.nombre == state_name).first()
    
    def get_role_by_id(self, role_id: int) -> Optional[Role]:
        """
        Obtiene un rol por su ID.

        Args:
            role_id (int): ID del rol.

        Returns:
            Optional[Role]: El rol si se encuentra, None en caso contrario.
        """
        return self.db.query(Role).filter(Role.id == role_id).first()
    
    def get_role_by_name(self, role_name: str) -> Optional[Role]:
        """
        Obtiene un rol por su nombre.

        Args:
            role_name (str): Nombre del rol.

        Returns:
            Optional[Role]: El rol si se encuentra, None en caso contrario.
        """
        return self.db.query(Role).filter(Role.nombre == role_name).first()
