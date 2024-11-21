"""
Módulo principal de la aplicación AgroInSight.

Este módulo inicializa la aplicación FastAPI, configura los routers
y los manejadores de excepciones.

Attributes:
    app (FastAPI): Instancia principal de la aplicación FastAPI.
    logger (logging.Logger): Logger configurado para este módulo.

"""

from fastapi import FastAPI, HTTPException, Request
from app.user.infrastructure.api import user_router
from app.farm.infrastructure.api import router as farm_router
from app.plot.infrastructure.api import router as plot_router
from app.cultural_practices.infrastructure.api import router as cultural_practices_router
from app.crop.infrastructure.api import router as crop_router
from app.measurement.infrastructure.api import measurement_router
from app.fall_armyworm.infrastructure.api import router as fall_armyworm_router
from app.soil_analysis.infrastructure.api import router as soil_analysis_router
from app.weather.infrastructure.api import router as weather_router
from app.costs.infrastructure.api import router as costs_router
from app.reports.infrastructure.api import router as reports_router
from fastapi.exceptions import RequestValidationError
from app.infrastructure.common.exceptions_handler import (
    validation_exception_handler, 
    custom_http_exception_handler,
    custom_exception_handler,
    domain_exception_handler,
    user_state_exception_handler
)
from app.infrastructure.common.common_exceptions import DomainException, UserStateException
from app.infrastructure.scheduler.weather_scheduler import WeatherScheduler
from contextlib import asynccontextmanager
import logging
from app.infrastructure.middleware.logging_middleware import logging_middleware as log_middleware_func
from app.infrastructure.middleware.database_middleware import database_middleware as db_middleware_func
from app.logs.infrastructure.api import logs_router

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    weather_scheduler = WeatherScheduler()
    weather_scheduler.start()
    yield
    # Shutdown (if needed)

app = FastAPI(lifespan=lifespan)

# Define y registra el logging_middleware primero
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    return await log_middleware_func(request, call_next)

# Define y registra el database_middleware después
@app.middleware("http")
async def database_middleware(request: Request, call_next):
    return await db_middleware_func(request, call_next)

# Inclusión de routers
app.include_router(user_router)
app.include_router(farm_router)
app.include_router(plot_router)
app.include_router(cultural_practices_router)
app.include_router(crop_router)
app.include_router(measurement_router)
app.include_router(fall_armyworm_router)
app.include_router(soil_analysis_router)
app.include_router(weather_router)
app.include_router(costs_router)
app.include_router(reports_router)
app.include_router(logs_router)

@app.get("/")
def root():
    """
    Ruta raíz de la API.

    Returns:
        dict: Mensaje de bienvenida.

    """
    return {"message": "Bienvenido a AgroinSight"}

# Registro de manejadores de excepciones
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(UserStateException, user_state_exception_handler)
app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(HTTPException, custom_http_exception_handler)
app.add_exception_handler(Exception, custom_exception_handler)
