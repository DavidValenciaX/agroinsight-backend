from fastapi import FastAPI, HTTPException
from app.user.infrastructure.api import router
from fastapi.exceptions import RequestValidationError
from app.core.exceptions_handler import (
    validation_exception_handler, 
    custom_http_exception_handler,
    custom_exception_handler,
    domain_exception_handler
)
from app.user.domain.exceptions import DomainException

app = FastAPI()

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Bienvenido a AgroinSight"}

# Manejadores de excepciones (registrar los más específicos primero)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(HTTPException, custom_http_exception_handler)
app.add_exception_handler(Exception, custom_exception_handler)