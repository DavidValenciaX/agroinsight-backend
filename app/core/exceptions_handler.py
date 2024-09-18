from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from app.user.domain.exceptions import UserAlreadyExistsException, ConfirmationError
import traceback
from app.core.security.security_utils import PasswordValidationError

async def validation_exception_handler(request: Request, exc: ValidationError):
    # Formatear la respuesta de errores de Pydantic para que el frontend entienda los detalles del error
    errors = exc.errors()
    formatted_errors = []
    
    for error in errors:
        formatted_errors.append({
            "field": ".".join(map(str, error["loc"])),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "route": str(request.url),
                "status_code": 422,
                "errors": formatted_errors,
                "message": "Error en la validación de los datos de entrada"
            }
        },
    )
    
async def password_validation_exception_handler(request: Request, exc: PasswordValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "route": str(request.url),
                "status_code": 400,
                "message": "Error en la validación de la contraseña",
                "details": exc.errors
            }
        },
    )

async def custom_exception_handler(request: Request, exc: Exception):
    # Manejador genérico para cualquier excepción no capturada
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "route": str(request.url),
                "status_code": 500,
                "message": "Error interno del servidor",
                "details": str(exc),
                "traceback": traceback.format_exc()  # útil para depurar
            }
        },
    )

async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "route": str(request.url),
                "status_code": exc.status_code,
                "message": exc.detail,
            }
        },
    )

async def business_exception_handler(request: Request, exc: UserAlreadyExistsException):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "route": str(request.url),
                "status_code": 400,
                "message": str(exc)
            }
        }
    )

async def confirmation_error_handler(request: Request, exc: ConfirmationError):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "route": str(request.url),
                "status_code": 500,
                "message": str(exc)
            }
        }
    )
