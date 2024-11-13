import httpx
from sqlalchemy.orm import Session
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from app.weather.domain.schemas import WeatherAPIResponse
import os
from dotenv import load_dotenv

load_dotenv(override=True)


class TestOpenWeatherMapAPIUseCase:
    """Caso de uso para probar la conexión con la API de OpenWeatherMap.
    
    Este caso de uso realiza una llamada de prueba a la API de OpenWeatherMap
    usando coordenadas de ejemplo para verificar la conectividad y el formato
    de respuesta.
    
    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
        api_key (str): Clave de API para OpenWeatherMap.
        base_url (str): URL base de la API de OpenWeatherMap.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        self.api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/3.0/onecall"
        
        if not self.api_key:
            raise DomainException(
                message="No se encontró la clave de API de OpenWeatherMap",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def test_api_connection(self) -> WeatherAPIResponse:
        """Prueba la conexión con la API de OpenWeatherMap.
        
        Realiza una llamada de prueba a la API usando coordenadas de ejemplo
        (Bogotá, Colombia) para verificar la conectividad y el formato de respuesta.

        Returns:
            WeatherAPIResponse: Respuesta formateada de la API.

        Raises:
            DomainException: Si hay un error al conectar con la API o procesar la respuesta.
        """
        # Coordenadas de ejemplo (Bogotá, Colombia)
        lat = 4.6097
        lon = -74.0817
        
        params = {
            "lat": lat,
            "lon": lon,
            "exclude": "minutely,hourly,daily,alerts",  # Excluimos datos que no necesitamos
            "appid": self.api_key,
            "units": "metric"  # Para obtener temperaturas en Celsius
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params)
                
                if response.status_code != 200:
                    raise DomainException(
                        message=f"Error al conectar con la API de OpenWeatherMap: {response.text}",
                        status_code=status.HTTP_502_BAD_GATEWAY
                    )
                
                data = response.json()
                return WeatherAPIResponse(
                    success=True,
                    message="Conexión exitosa con la API de OpenWeatherMap",
                    data=data
                )
                
        except httpx.RequestError as e:
            raise DomainException(
                message=f"Error de conexión con la API de OpenWeatherMap: {str(e)}",
                status_code=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            raise DomainException(
                message=f"Error al procesar la respuesta de la API: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 