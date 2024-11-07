from typing import Optional
from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.infrastructure.common.common_exceptions import DomainException
from app.user.application.services.user_service import UserService
from app.user.infrastructure.orm_models import Role
from app.user.infrastructure.sql_repository import UserRepository
from fastapi import status

class FarmService:
    """Servicio para la lógica de negocio relacionada con las fincas.

    Esta clase proporciona métodos para verificar roles de usuarios en fincas
    y obtener roles específicos necesarios para la gestión de fincas.

    Attributes:
        db (Session): Sesión de base de datos.
        user_repository (UserRepository): Repositorio para operaciones con usuarios.
        user_service (UserService): Servicio para lógica de negocio de usuarios.
        farm_repository (FarmRepository): Repositorio para operaciones con fincas.
    """

    def __init__(self, db: Session):
        """Inicializa el servicio de fincas con las dependencias necesarias.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        self.user_repository = UserRepository(db)
        self.user_service = UserService(db)
        self.farm_repository = FarmRepository(db)

    def user_is_farm_admin(self, user_id: int, farm_id: int) -> bool:
        """Verifica si un usuario tiene rol de administrador en una finca.

        Args:
            user_id (int): ID del usuario a verificar.
            farm_id (int): ID de la finca a verificar.

        Returns:
            bool: True si el usuario es administrador de la finca, False en caso contrario.
        """
        admin_role = self.get_admin_role()
        return self.farm_repository.get_user_farm_role(user_id, farm_id, admin_role.id) is not None
    
    def user_is_farm_worker(self, user_id: int, farm_id: int) -> bool:
        """Verifica si un usuario tiene rol de trabajador en una finca.

        Args:
            user_id (int): ID del usuario a verificar.
            farm_id (int): ID de la finca a verificar.

        Returns:
            bool: True si el usuario es trabajador de la finca, False en caso contrario.
        """
        worker_role = self.get_worker_role()
        return self.farm_repository.get_user_farm_role(user_id, farm_id, worker_role.id) is not None
    
    def get_admin_role(self) -> Optional[Role]:
        """Obtiene el rol de administrador de finca.

        Returns:
            Optional[Role]: Rol de administrador de finca.

        Raises:
            DomainException: Si no se puede obtener el rol de administrador.
        """
        rol_administrador_finca = self.user_repository.get_role_by_name(self.user_service.ADMIN_ROLE_NAME)
        if not rol_administrador_finca:
            raise DomainException(
                message="No se pudo obtener el rol de Administrador de Finca.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return rol_administrador_finca
    
    def get_worker_role(self) -> Optional[Role]:
        """Obtiene el rol de trabajador de finca.

        Returns:
            Optional[Role]: Rol de trabajador de finca.

        Raises:
            DomainException: Si no se puede obtener el rol de trabajador.
        """
        worker_role = self.user_repository.get_role_by_name(self.user_service.WORKER_ROLE_NAME)
        if not worker_role:
            raise DomainException(
                message="No se pudo obtener el rol de Trabajador de Finca.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return worker_role
