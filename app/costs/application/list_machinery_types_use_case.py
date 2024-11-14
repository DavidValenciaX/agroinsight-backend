from sqlalchemy.orm import Session
from app.costs.domain.schemas import MachineryTypeListResponse
from app.costs.infrastructure.sql_repository import CostsRepository
from app.infrastructure.mappers.response_mappers import map_machinery_type_to_response
from app.user.domain.schemas import UserInDB

class ListMachineryTypesUseCase:
    """Caso de uso para listar los tipos de maquinaria agrícola."""

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias."""
        self.db = db
        self.costs_repository = CostsRepository(db)

    def list_machinery_types(self, current_user: UserInDB) -> MachineryTypeListResponse:
        """Lista todos los tipos de maquinaria agrícola.

        Args:
            current_user (UserInDB): Usuario actual autenticado.

        Returns:
            MachineryTypeListResponse: Lista de tipos de maquinaria.
        """
        machinery_types = self.costs_repository.get_machinery_types()
        machinery_type_responses = [map_machinery_type_to_response(mt) for mt in machinery_types]
        return MachineryTypeListResponse(machinery_types=machinery_type_responses)