import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from app.infrastructure.common.datetime_utils import datetime_utc_time
from app.weather.domain.schemas import WeatherLogCreate
from app.weather.infrastructure.sql_repository import WeatherRepository
import os
from dotenv import load_dotenv
from app.weather.application.services.weather_measurement_service import WeatherMeasurementService

load_dotenv(override=True)

class RecordWeatherUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.repository = WeatherRepository(db)
        self.weather_measurement_service = WeatherMeasurementService(db)
        self.api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/3.0/onecall"

        if not self.api_key:
            raise DomainException(
                message="No se encontró la clave de API de OpenWeatherMap",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def record_weather_data(self, lote_id: int, lat: float, lon: float) -> WeatherLogCreate:
        """Registra los datos meteorológicos actuales para un lote específico."""
        try:
            # Validar unidades de medida
            self.weather_measurement_service.validate_weather_units()
            
            weather_data = await self._fetch_weather_data(lat, lon)
            current = weather_data['current']
            
            # Crear el registro meteorológico con las unidades correspondientes
            weather_log = WeatherLogCreate(
                lote_id=lote_id,
                fecha=datetime_utc_time.date(),
                hora=datetime_utc_time.time(),
                temperatura=current['temp'],
                temperatura_sensacion=current['feels_like'],
                temperatura_unidad_id=self.weather_measurement_service.TEMPERATURE_CELSIUS_ID,
                presion_atmosferica=current['pressure'],
                presion_unidad_id=self.weather_measurement_service.PRESSURE_HPA_ID,
                humedad_relativa=current['humidity'],
                humedad_unidad_id=self.weather_measurement_service.HUMIDITY_PERCENT_ID,
                indice_uv=current['uvi'],
                nubosidad=current['clouds'],
                nubosidad_unidad_id=self.weather_measurement_service.CLOUDINESS_PERCENT_ID,
                velocidad_viento=current['wind_speed'],
                velocidad_viento_unidad_id=self.weather_measurement_service.WIND_SPEED_MS_ID,
                direccion_viento=current['wind_deg'],
                direccion_viento_unidad_id=self.weather_measurement_service.WIND_DIRECTION_DEGREE_ID,
                rafaga_viento=current.get('wind_gust'),
                rafaga_viento_unidad_id=self.weather_measurement_service.WIND_SPEED_MS_ID,
                visibilidad=current.get('visibility'),
                visibilidad_unidad_id=self.weather_measurement_service.VISIBILITY_M_ID,
                punto_rocio=current.get('dew_point'),
                punto_rocio_unidad_id=self.weather_measurement_service.TEMPERATURE_CELSIUS_ID,
                descripcion_clima=current['weather'][0]['description'],
                codigo_clima=str(current['weather'][0]['id'])
            )

            return self.repository.create_weather_log(weather_log)

        except Exception as e:
            raise DomainException(
                message=f"Error al registrar datos meteorológicos: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def _fetch_weather_data(self, lat: float, lon: float) -> dict:
        """Obtiene los datos meteorológicos de la API de OpenWeatherMap."""
        params = {
            "lat": lat,
            "lon": lon,
            "exclude": "minutely,hourly,daily,alerts",
            "appid": self.api_key,
            "units": "metric"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            
            if response.status_code != 200:
                raise DomainException(
                    message=f"Error al obtener datos de la API: {response.text}",
                    status_code=status.HTTP_502_BAD_GATEWAY
                )
            
            return response.json()
