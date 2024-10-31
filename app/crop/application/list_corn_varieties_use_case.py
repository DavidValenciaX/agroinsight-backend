from sqlalchemy.orm import Session
from app.crop.infrastructure.sql_repository import CropRepository
from app.crop.domain.schemas import CornVarietyListResponse
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class ListCornVarietiesUseCase:
    """Caso de uso para listar las variedades de maíz.

    Esta clase maneja la lógica de negocio necesaria para obtener todas las variedades de maíz
    disponibles en el sistema.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
        crop_repository (CropRepository): Repositorio para operaciones con cultivos.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        self.crop_repository = CropRepository(db)

    def list_corn_varieties(self) -> CornVarietyListResponse:
        """Lista todas las variedades de maíz disponibles.

        Returns:
            CornVarietyListResponse: Objeto con la lista de variedades de maíz.

        Raises:
            DomainException: Si ocurre un error al obtener las variedades.
        """
        varieties = self.crop_repository.get_all_corn_varieties()
        if varieties is None:
            raise DomainException(
                message="Error al obtener las variedades de maíz",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        if len(varieties) == 0:
            raise DomainException(
                message="No hay variedades de maíz registradas",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        return CornVarietyListResponse(varieties=varieties)