from sqlalchemy.orm import Session
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class MeasurementService:
    
    # constantes de categorias de unidades de medida
    UNIT_CATEGORY_LENGTH_NAME = "Longitud"
    UNIT_CATEGORY_AREA_NAME = "Área"
    UNIT_CATEGORY_VOLUME_NAME = "Volumen"
    UNIT_CATEGORY_MASS_NAME = "Masa"
    UNIT_CATEGORY_TIME_NAME = "Tiempo"
    UNIT_CATEGORY_TEMPERATURE_NAME = "Temperatura"
    UNIT_CATEGORY_PLANTING_DENSITY_NAME = "Densidad de siembra"
    UNIT_CATEGORY_CURRENCY_NAME = "Moneda"
    UNIT_CATEGORY_YIELD_NAME = "Rendimiento"
    
    def __init__(self, db: Session):
        self.db = db
        
    def validate_unit_category(self, unit_of_measure, expected_category: str) -> None:
        if unit_of_measure.categoria.nombre != expected_category:
            raise DomainException(
                message=f"La unidad de medida debe ser de tipo {expected_category}.",
                status_code=status.HTTP_400_BAD_REQUEST
            )