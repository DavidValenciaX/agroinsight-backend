from sqlalchemy.orm import Session
from app.crop.infrastructure.sql_repository import CropRepository
from app.crop.domain.schemas import CornVarietyListResponse
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class ListCornVarietiesUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.crop_repository = CropRepository(db)

    def list_corn_varieties(self) -> CornVarietyListResponse:
        """
        Lista todas las variedades de maíz disponibles.

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