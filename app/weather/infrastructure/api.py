from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.user.domain.schemas import UserInDB
from app.weather.domain.schemas import WeatherAPIResponse, WeatherLogsListResponse
from app.weather.application.test_open_weather_map_api_use_case import TestOpenWeatherMapAPIUseCase
from app.weather.application.get_current_weather_use_case import GetCurrentWeatherUseCase
from app.weather.application.get_weather_logs_use_case import GetWeatherLogsUseCase
from datetime import date

router = APIRouter(tags=["weather"])

@router.get("/weather/test-api", response_model=WeatherAPIResponse)
async def test_weather_api(
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> WeatherAPIResponse:
    """
    Prueba la conexión con la API de OpenWeatherMap.
    
    Este endpoint realiza una llamada de prueba a la API de OpenWeatherMap
    usando coordenadas de ejemplo para verificar la conectividad.
    
    Args:
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario autenticado actual.
        
    Returns:
        WeatherAPIResponse: Respuesta de la prueba de conexión.
    """
    use_case = TestOpenWeatherMapAPIUseCase(db)
    return await use_case.test_api_connection() 

@router.get("/weather/current", response_model=WeatherAPIResponse)
async def get_current_weather(
    lat: float = Query(..., description="Latitud de la ubicación"),
    lon: float = Query(..., description="Longitud de la ubicación"),
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> WeatherAPIResponse:
    """
    Obtiene los datos meteorológicos actuales para una ubicación específica.
    
    Args:
        lat (float): Latitud de la ubicación.
        lon (float): Longitud de la ubicación.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario autenticado actual.
        
    Returns:
        WeatherAPIResponse: Datos meteorológicos actuales.
    """
    use_case = GetCurrentWeatherUseCase(db)
    return await use_case.get_current_weather(lat, lon) 

@router.get("/weather/logs/{lote_id}", response_model=WeatherLogsListResponse)
async def get_weather_logs(
    lote_id: int,
    start_date: date = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> WeatherLogsListResponse:
    """
    Obtiene los registros meteorológicos de un lote en un rango de fechas.

    Args:
        lote_id (int): ID del lote
        start_date (date): Fecha de inicio
        end_date (date): Fecha de fin
        db (Session): Sesión de base de datos
        current_user (UserInDB): Usuario autenticado actual

    Returns:
        WeatherLogsListResponse: Lista de registros meteorológicos
    """
    use_case = GetWeatherLogsUseCase(db)
    return await use_case.get_weather_logs(lote_id, start_date, end_date) 