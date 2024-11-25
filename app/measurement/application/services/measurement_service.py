from sqlalchemy.orm import Session
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

from app.measurement.infrastructure.orm_models import UnitOfMeasure
from app.measurement.infrastructure.sql_repository import MeasurementRepository

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
    
    # Abreviaturas de Monedas
    UNIT_SYMBOL_METER = "m"
    UNIT_SYMBOL_KILOMETER = "km"
    UNIT_SYMBOL_CENTIMETER = "cm"
    UNIT_SYMBOL_MILLIMETER = "mm"
    UNIT_SYMBOL_INCH = "in"
    UNIT_SYMBOL_FOOT = "ft"
    # Área
    UNIT_SYMBOL_SQUARE_METER = "m²"
    UNIT_SYMBOL_SQUARE_KILOMETER = "km²"
    UNIT_SYMBOL_HECTARE = "ha"
    UNIT_SYMBOL_ACRE = "ac"
    # Volumen
    UNIT_SYMBOL_LITER = "L"
    UNIT_SYMBOL_MILLILITER = "mL"
    UNIT_SYMBOL_CUBIC_METER = "m³"
    UNIT_SYMBOL_GALLON = "gal"
    UNIT_SYMBOL_BAG_60K_SEEDS = "bolsa 60k sem"
    # Masa
    UNIT_SYMBOL_KILOGRAM = "kg"
    UNIT_SYMBOL_GRAM = "g"
    UNIT_SYMBOL_TON = "t"
    UNIT_SYMBOL_POUND = "lb"
    UNIT_SYMBOL_BULK_50_KILOGRAMS = "bulto 50kg"
    # Tiempo
    UNIT_SYMBOL_SECOND = "s"
    UNIT_SYMBOL_MINUTE = "min"
    UNIT_SYMBOL_HOUR = "h"
    UNIT_SYMBOL_DAY = "d"
    # Temperatura
    UNIT_SYMBOL_CELSIUS = "°C"
    UNIT_SYMBOL_FAHRENHEIT = "°F"
    UNIT_SYMBOL_KELVIN = "K"
    # Densidad de siembra
    UNIT_SYMBOL_PLANTS_PER_HECTARE = "plantas/ha"
    UNIT_SYMBOL_SEEDS_PER_HECTARE = "semillas/ha"
    UNIT_SYMBOL_SEEDS_PER_SQUARE_METER = "semillas/m²"
    # Moneda
    UNIT_SYMBOL_COP = "COP"
    UNIT_SYMBOL_MXN = "MXN"
    UNIT_SYMBOL_USD = "USD"
    UNIT_SYMBOL_EUR = "EUR"
    UNIT_SYMBOL_GBP = "GBP"
    # Rendimiento
    UNIT_SYMBOL_TONS_PER_HECTARE = "t/ha"
    UNIT_SYMBOL_KILOGRAMS_PER_HECTARE = "kg/ha"
    # Presión 
    UNIT_SYMBOL_HECTOPASCAL = "hPa"
    UNIT_SYMBOL_MILLIBAR = "mbar"
    # Porcentaje
    UNIT_SYMBOL_PERCENTAGE = "%"
    # Velocidad
    UNIT_SYMBOL_METERS_PER_SECOND = "m/s"
    UNIT_SYMBOL_KILOMETERS_PER_HOUR = "km/h"
    UNIT_SYMBOL_MILES_PER_HOUR = "mph"
    # Ángulo
    UNIT_SYMBOL_DEGREE = "°"
    # Tasa de precipitación
    UNIT_SYMBOL_MILLIMETERS_PER_HOUR = "mm/h"
    
    
    def __init__(self, db: Session):
        """Inicializa el servicio de medidas con la sesión de base de datos.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        self.measurement_repository = MeasurementRepository(db)
        
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
            
    def get_default_currency(self) -> UnitOfMeasure:
        """Obtiene la moneda por defecto (COP)"""
        # Obtener la categoría de moneda
        currency_category = self.measurement_repository.get_unit_category_by_name(
            self.UNIT_CATEGORY_CURRENCY_NAME
        )
        if not currency_category:
            raise DomainException(
                message="No se encontró la categoría de moneda",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        # Obtener la moneda COP
        cop_currency = self.measurement_repository.get_unit_of_measure_by_name(
            self.UNIT_COP
        )
        if not cop_currency:
            raise DomainException(
                message="No se encontró la moneda COP",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        return cop_currency