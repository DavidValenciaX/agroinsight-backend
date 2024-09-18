# app/core/exceptions_handler.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback
from app.user.domain.exceptions import ConfirmationError, UserAlreadyExistsException

async def validation_exception_handler(request: Request, exc: RequestValidationError):
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

async def custom_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "route": str(request.url),
                "status_code": 500,
                "message": "Error interno del servidor",
                "errors": [
                    {
                        "message": str(exc),
                        "type": "exception",
                        "traceback": traceback.format_exc()
                    }
                ]
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
                "errors": []
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
                "message": str(exc),
                "errors": []
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
                "message": str(exc),
                "errors": []
            }
        }
    )
