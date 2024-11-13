from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.user.domain.schemas import UserInDB
from app.weather.domain.schemas import WeatherAPIResponse
from app.weather.application.test_open_weather_map_api_use_case import TestOpenWeatherMapAPIUseCase

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