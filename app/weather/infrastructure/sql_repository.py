from sqlalchemy.orm import Session
from app.weather.infrastructure.orm_models import WeatherLog
from app.weather.domain.schemas import WeatherLogCreate

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