from sqlalchemy.orm import Session
from app.weather.infrastructure.orm_models import WeatherLog
from app.weather.domain.schemas import WeatherLogCreate
from datetime import date

class WeatherRepository:
    """Repositorio para gestionar operaciones de base de datos relacionadas con registros meteorológicos.
    
    Esta clase maneja todas las operaciones de base de datos relacionadas con
    los registros meteorológicos.
    
    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
    """

    def __init__(self, db: Session):
        """Inicializa el repositorio con una sesión de base de datos.
        
        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db 

    def create_weather_log(self, weather_data: WeatherLogCreate) -> WeatherLog:
        """Crea un nuevo registro meteorológico."""
        db_weather = WeatherLog(**weather_data.model_dump())
        self.db.add(db_weather)
        self.db.commit()
        self.db.refresh(db_weather)
        return db_weather

    def get_latest_weather_log(self, lote_id: int) -> WeatherLog:
        """Obtiene el último registro meteorológico para un lote específico."""
        return self.db.query(WeatherLog)\
            .filter(WeatherLog.lote_id == lote_id)\
            .order_by(WeatherLog.fecha.desc(), WeatherLog.hora.desc())\
            .first() 

    def get_weather_logs_by_date_range(
        self, 
        lote_id: int, 
        start_date: date, 
        end_date: date
    ) -> list[WeatherLog]:
        """Obtiene los registros meteorológicos de un lote en un rango de fechas."""
        return self.db.query(WeatherLog)\
            .filter(
                WeatherLog.lote_id == lote_id,
                WeatherLog.fecha >= start_date,
                WeatherLog.fecha <= end_date
            )\
            .order_by(WeatherLog.fecha.asc(), WeatherLog.hora.asc())\
            .all()