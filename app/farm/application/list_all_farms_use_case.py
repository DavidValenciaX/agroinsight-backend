from sqlalchemy.orm import Session
from app.farm.application.services.farm_service import FarmService
from app.farm.infrastructure.sql_repository import FarmRepository
from app.farm.domain.schemas import FarmListResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.mappers.response_mappers import map_farm_to_response

class ListAllFarmsUseCase:
    """Caso de uso para listar todas las fincas donde un usuario es administrador.

    Esta clase maneja la lógica de negocio necesaria para obtener una lista completa
    de las fincas donde un usuario específico tiene rol de administrador.

    Attributes:
        db (Session): Sesión de base de datos.
        farm_repository (FarmRepository): Repositorio para operaciones con fincas.
        farm_service (FarmService): Servicio para lógica de negocio de fincas.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        self.farm_repository = FarmRepository(db)
        self.farm_service = FarmService(db)

    def list_all_farms(self, current_user: UserInDB) -> FarmListResponse:
        """Lista todas las fincas donde el usuario es administrador.

        Args:
            current_user (UserInDB): Usuario actual que solicita la lista de fincas.

        Returns:
            FarmListResponse: Respuesta que incluye:
                - Lista completa de fincas
                - Total de fincas
        """
        
        # Obtener id del rol de administrador de finca
        admin_role = self.farm_service.get_admin_role()

        # Obtener todas las fincas donde el usuario es administrador
        farms = self.farm_repository.list_farms_by_role(current_user.id, admin_role.id)
        
        # Mapear las fincas a su formato de respuesta
        farm_responses = [map_farm_to_response(farm) for farm in farms]

        return FarmListResponse(
            farms=farm_responses,
            total_farms=len(farms)
        ) 