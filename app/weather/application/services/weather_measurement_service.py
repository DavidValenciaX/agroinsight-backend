from sqlalchemy.orm import Session
from app.measurement.application.services.measurement_service import MeasurementService
from app.measurement.infrastructure.sql_repository import MeasurementRepository
from app.core.exceptions import DomainException
from fastapi import status

class WeatherMeasurementService:
    """Servicio para gestionar las unidades de medida meteorológicas."""

    def __init__(self, db: Session):
        self.db = db
        self.measurement_service = MeasurementService(db)
        self.measurement_repository = MeasurementRepository(db)
        
        # Inicializar IDs de unidades
        self._initialize_unit_ids()

    def _initialize_unit_ids(self):
        """Inicializa los IDs de las unidades de medida necesarias."""
        # Temperatura (Celsius)
        temp_unit = self.measurement_repository.get_unit_of_measure_by_name(self.measurement_service.UNIT_CELSIUS)
        self.TEMPERATURE_CELSIUS_ID = temp_unit.id if temp_unit else None

        # Presión (hPa)
        pressure_unit = self.measurement_repository.get_unit_of_measure_by_name(self.measurement_service.UNIT_HECTOPASCAL)
        self.PRESSURE_HPA_ID = pressure_unit.id if pressure_unit else None

        # Humedad (%)
        humidity_unit = self.measurement_repository.get_unit_of_measure_by_name(self.measurement_service.UNIT_PERCENTAGE)
        self.HUMIDITY_PERCENT_ID = humidity_unit.id if humidity_unit else None

        # Velocidad del viento (m/s)
        wind_speed_unit = self.measurement_repository.get_unit_of_measure_by_name(self.measurement_service.UNIT_METERS_PER_SECOND)
        self.WIND_SPEED_MS_ID = wind_speed_unit.id if wind_speed_unit else None

        # Dirección del viento (grados)
        wind_dir_unit = self.measurement_repository.get_unit_of_measure_by_name(self.measurement_service.UNIT_DEGREE)
        self.WIND_DIRECTION_DEGREE_ID = wind_dir_unit.id if wind_dir_unit else None

        # Precipitación (mm/h)
        precip_unit = self.measurement_repository.get_unit_of_measure_by_name(self.measurement_service.UNIT_MILLIMETERS_PER_HOUR)
        self.PRECIPITATION_MMH_ID = precip_unit.id if precip_unit else None

        # Nubosidad (%)
        cloud_unit = self.measurement_repository.get_unit_of_measure_by_name(self.measurement_service.UNIT_PERCENTAGE)
        self.CLOUDINESS_PERCENT_ID = cloud_unit.id if cloud_unit else None

        # Visibilidad (metros)
        visibility_unit = self.measurement_repository.get_unit_of_measure_by_name(self.measurement_service.UNIT_METER)
        self.VISIBILITY_M_ID = visibility_unit.id if visibility_unit else None

    def validate_weather_units(self):
        """Valida que todas las unidades necesarias existan y sean del tipo correcto."""
        # Temperatura
        temp_unit = self.measurement_repository.get_unit_of_measure_by_name(self.measurement_service.UNIT_CELSIUS)
        self.measurement_service.validate_unit_category(temp_unit, self.measurement_service.UNIT_CATEGORY_TEMPERATURE_NAME)

        # Presión
        pressure_unit = self.measurement_repository.get_unit_of_measure_by_name(self.measurement_service.UNIT_HECTOPASCAL)
        self.measurement_service.validate_unit_category(pressure_unit, "Presión")

        # Humedad
        humidity_unit = self.measurement_repository.get_unit_of_measure_by_name(self.measurement_service.UNIT_PERCENTAGE)
        self.measurement_service.validate_unit_category(humidity_unit, "Porcentaje")

        # Velocidad del viento
        wind_speed_unit = self.measurement_repository.get_unit_of_measure_by_name(self.measurement_service.UNIT_METERS_PER_SECOND)
        self.measurement_service.validate_unit_category(wind_speed_unit, "Velocidad")

        # Dirección del viento
        wind_dir_unit = self.measurement_repository.get_unit_of_measure_by_name(self.measurement_service.UNIT_DEGREE)
        self.measurement_service.validate_unit_category(wind_dir_unit, "Ángulo")

        # Precipitación
        precip_unit = self.measurement_repository.get_unit_of_measure_by_name(self.measurement_service.UNIT_MILLIMETERS_PER_HOUR)
        self.measurement_service.validate_unit_category(precip_unit, self.measurement_service.UNIT_CATEGORY_PRECIPITATION_RATE_NAME)

        # Validar que todos los IDs se hayan inicializado correctamente
        if any(id is None for id in [
            self.TEMPERATURE_CELSIUS_ID,
            self.PRESSURE_HPA_ID,
            self.HUMIDITY_PERCENT_ID,
            self.WIND_SPEED_MS_ID,
            self.WIND_DIRECTION_DEGREE_ID,
            self.PRECIPITATION_MMH_ID,
            self.CLOUDINESS_PERCENT_ID,
            self.VISIBILITY_M_ID
        ]):
            raise DomainException(
                message="No se pudieron inicializar todas las unidades de medida necesarias",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )