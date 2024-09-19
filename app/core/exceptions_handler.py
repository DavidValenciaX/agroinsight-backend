# app/core/exceptions_handler.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback
from app.user.domain.exceptions import DomainException
from typing import Dict, List

CUSTOM_MESSAGES = {
    'missing': 'El campo es requerido',
    'value_error.missing': 'El campo es requerido'
    # Agregar otros tipos de error y mensajes personalizados si es necesario
}

def convert_errors(errors: List[Dict], custom_messages: Dict[str, str]) -> List[Dict]:
    new_errors = []
    for error in errors:
        error_type = error['type']
        custom_message = custom_messages.get(error_type)
        if custom_message:
            ctx = error.get('ctx', {})
            error['msg'] = custom_message.format(**ctx) if ctx else custom_message
        new_errors.append(error)
    return new_errors

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Reemplaza los mensajes de error con los personalizados
    errors = convert_errors(errors, CUSTOM_MESSAGES)
    formatted_errors = []

    for error in errors:
        formatted_errors.append({
            "field": error["loc"][-1],
            "message": error["msg"].split('\n')
        })

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "route": str(request.url),
                "status_code": 422,
                "message": "Error en la validación de los datos de entrada",
                "details": formatted_errors
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
                "details": [
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
                "details": []
            }
        },
    )
    
async def domain_exception_handler(request: Request, exc: DomainException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "route": str(request.url),
                "status_code": exc.status_code,
                "message": exc.message,
                "details": []
            }
        }
    )