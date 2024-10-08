from sqlalchemy.orm import Session
from fastapi import status
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserCreateByAdmin
from app.infrastructure.common.common_exceptions import DomainException, InsufficientPermissionsException, MissingTokenException, UserAlreadyRegisteredException, UserStateException
from app.infrastructure.security.security_utils import hash_password
from app.user.infrastructure.orm_models import User


class AdminCreatesUserUseCase:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)

    def admin_creates_user(self, user_data: UserCreateByAdmin, current_user) -> SuccessResponse:
        if not current_user:
            raise MissingTokenException()

        # Verificar que el usuario actual tiene roles de administrador
        admin_roles = self.user_repository.get_admin_roles()
        admin_role_ids = {admin_role.id for admin_role in admin_roles}
        if not any(role.id in admin_role_ids for role in current_user.roles):
            raise InsufficientPermissionsException()
            
        # Verificar si el correo electrónico ya existe
        existing_user = self.user_repository.get_user_by_email(user_data.email)
        if existing_user:
                raise UserAlreadyRegisteredException()

        # Verificar si el rol proporcionado es válido
        role = self.user_repository.get_role_by_id(user_data.role_id)
        if not role:
            raise DomainException(
                message="Rol proporcionado no válido.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Crear el usuario con estado "active"
        hashed_password = hash_password(user_data.password)
        active_state_id = self.user_repository.get_active_user_state_id()
        if not active_state_id:
            raise UserStateException(
                message="No se pudo encontrar el estado de usuario activo.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                user_state="unknown"
            )

        new_user = User(
            nombre=user_data.nombre,
            apellido=user_data.apellido,
            email=user_data.email,
            password=hashed_password,
            state_id=active_state_id,
        )

        created_user = self.user_repository.create_user(new_user)
        if not created_user:
            raise DomainException(
                message="Error al procesar la creación del usuario.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Asignar el rol especificado
        self.user_repository.assign_role_to_user(created_user.id, user_data.role_id)

        return SuccessResponse(
            message="Usuario creado y activado exitosamente."
        )