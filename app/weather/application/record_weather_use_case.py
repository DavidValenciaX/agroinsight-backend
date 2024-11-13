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

load_dotenv(override=True)

class RecordWeatherUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.repository = WeatherRepository(db)
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
            weather_data = await self._fetch_weather_data(lat, lon)
            current = weather_data['current']
            
            # Crear el registro meteorológico
            weather_log = WeatherLogCreate(
                lote_id=lote_id,
                fecha=datetime_utc_time.date(),
                hora=datetime_utc_time.time(),
                temperatura=current['temp'],
                temperatura_sensacion=current['feels_like'],
                presion_atmosferica=current['pressure'],
                humedad_relativa=current['humidity'],
                indice_uv=current['uvi'],
                nubosidad=current['clouds'],
                velocidad_viento=current['wind_speed'],
                direccion_viento=current['wind_deg'],
                rafaga_viento=current.get('wind_gust'),
                visibilidad=current.get('visibility'),
                punto_rocio=current.get('dew_point'),
                descripcion_clima=current['weather'][0]['description'],
                codigo_clima=current['weather'][0]['id']
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
