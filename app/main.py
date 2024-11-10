"""
Módulo principal de la aplicación AgroInSight.

Este módulo inicializa la aplicación FastAPI, configura los routers
y los manejadores de excepciones.

Attributes:
    app (FastAPI): Instancia principal de la aplicación FastAPI.
    logger (logging.Logger): Logger configurado para este módulo.

"""

from fastapi import FastAPI, HTTPException
from app.user.infrastructure.api import user_router
from app.farm.infrastructure.api import router as farm_router
from app.plot.infrastructure.api import router as plot_router
from app.cultural_practices.infrastructure.api import router as cultural_practices_router
from app.crop.infrastructure.api import router as crop_router
from app.measurement.infrastructure.api import measurement_router
from app.image_analysis.infrastructure.api import router as image_analysis_router
from fastapi.exceptions import RequestValidationError
from app.infrastructure.common.exceptions_handler import (
    validation_exception_handler, 
    custom_http_exception_handler,
    custom_exception_handler,
    domain_exception_handler,
    user_state_exception_handler
)
from app.infrastructure.common.common_exceptions import DomainException, UserStateException
import logging

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Creación de la instancia de FastAPI
app = FastAPI()

# Inclusión de routers
app.include_router(user_router)
app.include_router(farm_router)
app.include_router(plot_router)
app.include_router(cultural_practices_router)
app.include_router(crop_router)
app.include_router(measurement_router)
app.include_router(image_analysis_router)

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
