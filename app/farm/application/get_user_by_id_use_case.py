from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.user.domain.schemas import UserForFarmResponse
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException
from app.infrastructure.mappers.response_mappers import map_user_for_farm_to_response
from fastapi import status
from app.farm.application.services.farm_service import FarmService

class AdminGetUserByIdUseCase:
    """Caso de uso para obtener información de un usuario específico en una finca por un administrador.

    Esta clase maneja la lógica de negocio necesaria para que un administrador de una finca
    pueda obtener la información detallada de un usuario que pertenece a dicha finca.

    Attributes:
        db (Session): Sesión de base de datos.
        user_repository (UserRepository): Repositorio para operaciones con usuarios.
        farm_repository (FarmRepository): Repositorio para operaciones con fincas.
        farm_service (FarmService): Servicio para lógica de negocio de fincas.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        self.user_repository = UserRepository(db)
        self.farm_repository = FarmRepository(db)
        self.farm_service = FarmService(db)
        
    def admin_get_user_by_id(self, user_id: int, farm_id: int, current_user) -> UserForFarmResponse:
        """Obtiene la información de un usuario específico en una finca.

        Este método realiza las siguientes validaciones:
        1. Verifica que el usuario solicitado exista
        2. Confirma que el usuario solicitado pertenezca a la finca (como trabajador o administrador)
        3. Verifica que el usuario actual tenga permisos de administrador en la finca

        Args:
            user_id (int): ID del usuario que se quiere consultar.
            farm_id (int): ID de la finca donde se quiere consultar el usuario.
            current_user: Usuario que realiza la consulta.

        Returns:
            UserForFarmResponse: Información del usuario consultado incluyendo su rol en la finca.

        Raises:
            UserNotRegisteredException: Si el usuario solicitado no existe.
            DomainException: Si ocurre algún error de validación:
                - 400: El usuario no pertenece a la finca especificada
                - 403: El usuario actual no tiene permisos de administrador
        """
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            raise UserNotRegisteredException()
        
        # Verificar si el user_id es trabajador o administrador en la finca especificada
        if not self.farm_service.user_is_farm_worker(user_id, farm_id) and not self.farm_service.user_is_farm_admin(user_id, farm_id):
            raise DomainException(
                message="El usuario no es trabajador o administrador en la finca especificada",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar si el current_user es administrador en la finca especificada
        if not self.farm_service.user_is_farm_admin(current_user.id, farm_id):
            raise DomainException(
                message="No tienes permisos para obtener información de este usuario.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Obtener el rol específico del usuario en esta finca
        user_farm_role = self.farm_repository.get_user_farm(user_id, farm_id)
        
        return map_user_for_farm_to_response(user, user_farm_role.rol.nombre)
