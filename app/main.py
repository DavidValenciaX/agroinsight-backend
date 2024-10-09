"""
Módulo principal de la aplicación AgroInSight.

Este módulo inicializa la aplicación FastAPI, configura los routers
y los manejadores de excepciones.
"""

from fastapi import FastAPI, HTTPException
from app.user.infrastructure.user_api import user_router
from app.user.infrastructure.superuser_api import admin_router
from app.farm.infrastructure.api import router as farm_router
from app.plot.infrastructure.api import router as plot_router
from app.cultural_practices.infrastructure.api import router as cultural_practices_router
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(user_router)
app.include_router(admin_router)
app.include_router(farm_router)
app.include_router(plot_router)
app.include_router(cultural_practices_router)

@app.get("/")
def root():
    """
    Ruta raíz de la API.

    Returns:
        dict: Mensaje de bienvenida.
    """
    return {"message": "Bienvenido a AgroinSight"}

# Manejadores de excepciones (registrar los más específicos primero)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(UserStateException, user_state_exception_handler)
app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(HTTPException, custom_http_exception_handler)
app.add_exception_handler(Exception, custom_exception_handler)