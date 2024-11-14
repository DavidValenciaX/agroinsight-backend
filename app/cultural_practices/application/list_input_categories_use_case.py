from sqlalchemy.orm import Session
from app.cultural_practices.domain.schemas import AgriculturalInputCategoryListResponse
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.infrastructure.mappers.response_mappers import map_input_category_to_response
from app.user.domain.schemas import UserInDB

class ListInputCategoriesUseCase:
    """Caso de uso para listar las categorías de insumos agrícolas.

    Este caso de uso gestiona la lógica de negocio para recuperar todas las categorías de insumos,
    asegurando que se cumplan las validaciones necesarias antes de devolver la lista.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
        cultural_practice_repository (CulturalPracticesRepository): Repositorio para operaciones de prácticas culturales.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias."""
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)

    def list_categories(self, current_user: UserInDB) -> AgriculturalInputCategoryListResponse:
        """Lista todas las categorías de insumos agrícolas.

        Args:
            current_user (UserInDB): Usuario actual autenticado.

        Returns:
            AgriculturalInputCategoryListResponse: Lista de categorías de insumos.
        """
        categories = self.cultural_practice_repository.get_input_categories()
        category_responses = [map_input_category_to_response(category) for category in categories]
        return AgriculturalInputCategoryListResponse(categories=category_responses)