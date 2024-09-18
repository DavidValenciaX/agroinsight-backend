from fastapi import FastAPI, HTTPException
from app.user.infrastructure.api import router
from fastapi.exceptions import RequestValidationError
from app.core.exceptions_handler import (
    password_validation_exception_handler,
    validation_exception_handler, 
    custom_exception_handler,
    custom_http_exception_handler,
    business_exception_handler,
    confirmation_error_handler
)
from app.user.domain.exceptions import UserAlreadyExistsException, ConfirmationError
from app.core.security.security_utils import PasswordValidationError

app = FastAPI()

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Bienvenido a AgroinSight"}

# Manejadores de excepciones
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, custom_exception_handler)
app.add_exception_handler(HTTPException, custom_http_exception_handler)
app.add_exception_handler(UserAlreadyExistsException, business_exception_handler)
app.add_exception_handler(ConfirmationError, confirmation_error_handler)
app.add_exception_handler(PasswordValidationError, password_validation_exception_handler)