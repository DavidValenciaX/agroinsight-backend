from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.weather.application.record_weather_use_case import RecordWeatherUseCase
from app.infrastructure.db.connection import SessionLocal
from app.plot.infrastructure.sql_repository import PlotRepository
import asyncio
from contextlib import asynccontextmanager

class WeatherScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    async def record_weather_for_all_plots(self):
        """Registra el clima para todos los lotes activos."""
        @asynccontextmanager
        async def get_db():
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()
        
        async with get_db() as db:
            # Obtener todos los lotes activos
            plot_repository = PlotRepository(db)
            plots = plot_repository.list_plots()
            
            # Registrar el clima para cada lote
            weather_use_case = RecordWeatherUseCase(db)
            for plot in plots:
                await weather_use_case.record_weather_data(
                    lote_id=plot.id,
                    lat=plot.latitud,
                    lon=plot.longitud
                )

    def start(self):
        """Inicia el programador con las tareas configuradas."""
        # Programar la tarea para ejecutarse cada hora en el minuto 0
        self.scheduler.add_job(
            self.record_weather_for_all_plots,
            CronTrigger(minute=0),  # Ejecutar al inicio de cada hora
            id='weather_recording',
            name='Record weather data for all plots',
            replace_existing=True
        )
        
        self.scheduler.start()