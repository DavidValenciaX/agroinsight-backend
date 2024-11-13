from sqlalchemy.orm import Session
from app.measurement.application.services.measurement_service import MeasurementService
from app.measurement.infrastructure.sql_repository import MeasurementRepository

class WeatherMeasurementService:
    """Servicio para gestionar las unidades de medida meteorológicas."""

    # IDs de las unidades de medida en sistema métrico
    TEMPERATURE_CELSIUS_ID = 22  # Grado Celsius
    PRESSURE_HPA_ID = 32        # Hectopascal
    HUMIDITY_PERCENT_ID = 33    # Porcentaje
    WIND_SPEED_MS_ID = 34      # Metro por segundo
    WIND_DIRECTION_DEGREE_ID = 36  # Grado
    PRECIPITATION_MM_ID = 4     # Milímetro
    CLOUDINESS_PERCENT_ID = 33  # Porcentaje
    VISIBILITY_M_ID = 1         # Metro

    def __init__(self, db: Session):
        self.db = db
        self.measurement_service = MeasurementService(db)
        self.measurement_repository = MeasurementRepository(db)

    def validate_weather_units(self):
        """Valida que todas las unidades necesarias existan y sean del tipo correcto."""
        # Temperatura
        temp_unit = self.measurement_repository.get_unit_of_measure_by_id(self.TEMPERATURE_CELSIUS_ID)
        self.measurement_service.validate_unit_category(temp_unit, self.measurement_service.UNIT_CATEGORY_TEMPERATURE_NAME)

        # Presión
        pressure_unit = self.measurement_repository.get_unit_of_measure_by_id(self.PRESSURE_HPA_ID)
        self.measurement_service.validate_unit_category(pressure_unit, "Presión")

        # Humedad
        humidity_unit = self.measurement_repository.get_unit_of_measure_by_id(self.HUMIDITY_PERCENT_ID)
        self.measurement_service.validate_unit_category(humidity_unit, "Porcentaje")

        # Velocidad del viento
        wind_speed_unit = self.measurement_repository.get_unit_of_measure_by_id(self.WIND_SPEED_MS_ID)
        self.measurement_service.validate_unit_category(wind_speed_unit, "Velocidad")

        # Dirección del viento
        wind_dir_unit = self.measurement_repository.get_unit_of_measure_by_id(self.WIND_DIRECTION_DEGREE_ID)
        self.measurement_service.validate_unit_category(wind_dir_unit, "Ángulo")