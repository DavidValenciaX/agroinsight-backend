"""
Módulo principal de la aplicación AgroInSight.

Este módulo inicializa la aplicación FastAPI, configura los routers
y los manejadores de excepciones.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import os
from app.user.infrastructure.api import router as user_router
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

app = FastAPI()

# Ruta absoluta para mayor seguridad
site_directory = os.path.join(os.getcwd(), "site")

# Montar StaticFiles con html=True
app.mount("/MkDocs", StaticFiles(directory=site_directory, html=True), name="site")

app.include_router(user_router)
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