from sqlalchemy.orm import Session
from app.costs.domain.schemas import AgriculturalMachineryListResponse
from app.costs.infrastructure.sql_repository import CostsRepository
from app.infrastructure.mappers.response_mappers import map_agricultural_machinery_to_response
from app.user.domain.schemas import UserInDB

class ListAgriculturalMachineryUseCase:
    """Caso de uso para listar la maquinaria agrícola."""

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias."""
        self.db = db
        self.costs_repository = CostsRepository(db)

    def list_machinery(self, current_user: UserInDB) -> AgriculturalMachineryListResponse:
        """Lista toda la maquinaria agrícola.

        Args:
            current_user (UserInDB): Usuario actual autenticado.

        Returns:
            AgriculturalMachineryListResponse: Lista de maquinaria agrícola.
        """
        machinery = self.costs_repository.get_agricultural_machinery()
        machinery_responses = [map_agricultural_machinery_to_response(m) for m in machinery]
        return AgriculturalMachineryListResponse(machinery=machinery_responses)