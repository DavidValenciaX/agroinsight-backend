from sqlalchemy.orm import Session
from app.cultural_practices.domain.schemas import AgriculturalInputListResponse
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.infrastructure.mappers.response_mappers import map_agricultural_input_to_response
from app.user.domain.schemas import UserInDB

class ListAgriculturalInputsUseCase:
    """Caso de uso para listar los insumos agrícolas.

    Este caso de uso gestiona la lógica de negocio para recuperar todos los insumos agrícolas,
    asegurando que se cumplan las validaciones necesarias antes de devolver la lista.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
        cultural_practice_repository (CulturalPracticesRepository): Repositorio para operaciones de prácticas culturales.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias."""
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)

    def list_inputs(self, current_user: UserInDB) -> AgriculturalInputListResponse:
        """Lista todos los insumos agrícolas.

        Args:
            current_user (UserInDB): Usuario actual autenticado.

        Returns:
            AgriculturalInputListResponse: Lista de insumos agrícolas.
        """
        inputs = self.cultural_practice_repository.get_agricultural_inputs()
        input_responses = [map_agricultural_input_to_response(input) for input in inputs]
        return AgriculturalInputListResponse(inputs=input_responses) 