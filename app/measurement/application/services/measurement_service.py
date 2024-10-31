from sqlalchemy.orm import Session
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class MeasurementService:
    """Servicio para gestionar la lógica de negocio relacionada con las medidas.

    Este servicio proporciona métodos para validar y gestionar las unidades de medida y sus categorías.

    Attributes:
        UNIT_CATEGORY_LENGTH_NAME (str): Nombre de la categoría de unidad de medida para longitud.
        UNIT_CATEGORY_AREA_NAME (str): Nombre de la categoría de unidad de medida para área.
        UNIT_CATEGORY_VOLUME_NAME (str): Nombre de la categoría de unidad de medida para volumen.
        UNIT_CATEGORY_MASS_NAME (str): Nombre de la categoría de unidad de medida para masa.
        UNIT_CATEGORY_TIME_NAME (str): Nombre de la categoría de unidad de medida para tiempo.
        UNIT_CATEGORY_TEMPERATURE_NAME (str): Nombre de la categoría de unidad de medida para temperatura.
        UNIT_CATEGORY_PLANTING_DENSITY_NAME (str): Nombre de la categoría de unidad de medida para densidad de siembra.
        UNIT_CATEGORY_CURRENCY_NAME (str): Nombre de la categoría de unidad de medida para moneda.
        UNIT_CATEGORY_YIELD_NAME (str): Nombre de la categoría de unidad de medida para rendimiento.
        db (Session): Sesión de base de datos SQLAlchemy.
    """

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
        """Inicializa el servicio de medidas con la sesión de base de datos.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        
    def validate_unit_category(self, unit_of_measure, expected_category: str) -> None:
        """Valida que la unidad de medida pertenezca a la categoría esperada.

        Este método verifica si la categoría de la unidad de medida coincide con la categoría esperada.
        Si no coincide, se lanza una excepción.

        Args:
            unit_of_measure: La unidad de medida a validar.
            expected_category (str): La categoría esperada para la unidad de medida.

        Raises:
            DomainException: Si la unidad de medida no pertenece a la categoría esperada.
        """
        if unit_of_measure.categoria.nombre != expected_category:
            raise DomainException(
                message=f"La unidad de medida debe ser de tipo {expected_category}.",
                status_code=status.HTTP_400_BAD_REQUEST
            )