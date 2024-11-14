from datetime import date
from sqlalchemy.orm import Session
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from app.weather.domain.schemas import WeatherLogsListResponse
from app.weather.infrastructure.sql_repository import WeatherRepository

class GetWeatherLogsUseCase:
    """Caso de uso para obtener registros meteorológicos históricos."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = WeatherRepository(db)

    async def get_weather_logs(
        self, 
        lote_id: int, 
        start_date: date, 
        end_date: date
    ) -> WeatherLogsListResponse:
        """
        Obtiene los registros meteorológicos para un lote en un rango de fechas.

        Args:
            lote_id (int): ID del lote
            start_date (date): Fecha de inicio
            end_date (date): Fecha de fin

        Returns:
            WeatherLogsListResponse: Lista de registros meteorológicos
        """
        try:
            if start_date > end_date:
                raise DomainException(
                    message="La fecha de inicio debe ser anterior o igual a la fecha de fin",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            weather_logs = self.repository.get_weather_logs_by_date_range(
                lote_id=lote_id,
                start_date=start_date,
                end_date=end_date
            )

            return WeatherLogsListResponse(
                success=True,
                message="Registros meteorológicos obtenidos exitosamente",
                data=weather_logs
            )

        except Exception as e:
            if isinstance(e, DomainException):
                raise e
            raise DomainException(
                message=f"Error al obtener los registros meteorológicos: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )