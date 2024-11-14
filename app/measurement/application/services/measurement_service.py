from sqlalchemy.orm import Session
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

from app.measurement.infrastructure.orm_models import UnitOfMeasure

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
    UNIT_CATEGORY_PRESSURE_NAME = "Presión"
    UNIT_CATEGORY_PERCENTAGE_NAME = "Porcentaje"
    UNIT_CATEGORY_SPEED_NAME = "Velocidad"
    UNIT_CATEGORY_ANGLE_NAME = "Ángulo"
    UNIT_CATEGORY_PRECIPITATION_RATE_NAME = "Tasa de precipitación"

    # Unidades de Longitud
    UNIT_METER = "Metro"
    UNIT_KILOMETER = "Kilómetro"
    UNIT_CENTIMETER = "Centímetro"
    UNIT_MILLIMETER = "Milímetro"
    UNIT_INCH = "Pulgada"
    UNIT_FOOT = "Pie"

    # Unidades de Área
    UNIT_SQUARE_METER = "Metro cuadrado"
    UNIT_SQUARE_KILOMETER = "Kilómetro cuadrado"
    UNIT_HECTARE = "Hectárea"
    UNIT_ACRE = "Acre"

    # Unidades de Volumen
    UNIT_LITER = "Litro"
    UNIT_MILLILITER = "Mililitro"
    UNIT_CUBIC_METER = "Metro cúbico"
    UNIT_GALLON = "Galón"

    # Unidades de Masa
    UNIT_KILOGRAM = "Kilogramo"
    UNIT_GRAM = "Gramo"
    UNIT_TON = "Tonelada"
    UNIT_POUND = "Libra"

    # Unidades de Tiempo
    UNIT_SECOND = "Segundo"
    UNIT_MINUTE = "Minuto"
    UNIT_HOUR = "Hora"
    UNIT_DAY = "Día"

    # Unidades de Temperatura
    UNIT_CELSIUS = "Grado Celsius"
    UNIT_FAHRENHEIT = "Grado Fahrenheit"
    UNIT_KELVIN = "Kelvin"

    # Unidades de Densidad de Siembra
    UNIT_PLANTS_PER_HECTARE = "Plantas por hectárea"
    UNIT_SEEDS_PER_HECTARE = "Semillas por hectárea"
    UNIT_SEEDS_PER_SQUARE_METER = "Semillas por metro cuadrado"

    # Unidades de Moneda
    UNIT_COP = "Peso Colombiano"
    UNIT_MXN = "Peso Mexicano"
    UNIT_USD = "Dólar Estadounidense"
    UNIT_EUR = "Euro"
    UNIT_GBP = "Libra Esterlina"

    # Unidades de Rendimiento
    UNIT_TONS_PER_HECTARE = "Toneladas por hectárea"
    UNIT_KILOGRAMS_PER_HECTARE = "Kilogramos por hectárea"

    # Unidades de Presión
    UNIT_HECTOPASCAL = "Hectopascal"
    UNIT_MILLIBAR = "Milibar"

    # Unidades de Porcentaje
    UNIT_PERCENTAGE = "Porcentaje"

    # Unidades de Velocidad
    UNIT_METERS_PER_SECOND = "Metro por segundo"
    UNIT_KILOMETERS_PER_HOUR = "Kilómetro por hora"
    UNIT_MILES_PER_HOUR = "Milla por hora"

    # Unidades de Ángulo
    UNIT_DEGREE = "Grado"

    # Unidades de Tasa de Precipitación
    UNIT_MILLIMETERS_PER_HOUR = "Milímetro por hora"
    
    def __init__(self, db: Session):
        """Inicializa el servicio de medidas con la sesión de base de datos.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        
    def validate_unit_category(self, unit_of_measure: "UnitOfMeasure", expected_category: str) -> None:
        """Valida que la unidad de medida pertenezca a la categoría esperada.

        Este método verifica si la categoría de la unidad de medida coincide con la categoría esperada.
        Si no coincide, se lanza una excepción.

        Args:
            unit_of_measure (UnitOfMeasure): La unidad de medida a validar.
            expected_category (str): La categoría esperada para la unidad de medida.

        Raises:
            DomainException: Si la unidad de medida no pertenece a la categoría esperada.
        """
        if unit_of_measure.categoria.nombre != expected_category:
            raise DomainException(
                message=f"La unidad de medida debe ser de tipo {expected_category}.",
                status_code=status.HTTP_400_BAD_REQUEST
            )