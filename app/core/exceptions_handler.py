# app/core/exceptions_handler.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback
from app.user.domain.exceptions import DomainException
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

CUSTOM_MESSAGES = {
    'missing': 'El campo es requerido',
    'value_error.missing': 'El campo es requerido',
    'int_parsing': 'La entrada debe ser un número entero válido'
    # Agregar otros tipos de error y mensajes personalizados si es necesario
}

HTTP_CUSTOM_MESSAGES = {
    401: "No estás autenticado. Por favor, proporciona credenciales válidas.",
    403: "No tienes permisos para realizar esta acción.",
    404: "Recurso no encontrado.",
    405: "Método no permitido.",
    406: "No aceptable.",
    409: "Conflicto con el estado actual del recurso.",
    # Agrega más códigos de estado y mensajes según tus necesidades
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

def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Reemplaza los mensajes de error con los personalizados
    errors = convert_errors(errors, CUSTOM_MESSAGES)
    formatted_errors = []

    for error in errors:
        formatted_errors.append({
            "field": error["loc"][-1],
            "type": error['type'],
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

def custom_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error en la ruta {request.url}: {str(exc)}")
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

def custom_http_exception_handler(request: Request, exc: HTTPException):
    # Obtener el mensaje personalizado basado en el status_code
    message = HTTP_CUSTOM_MESSAGES.get(exc.status_code, exc.detail)
    logger.info(f"HTTPException en {request.url}: {message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "route": str(request.url),
                "status_code": exc.status_code,
                "message": message,
                "details": []
            }
        },
    )

    
def domain_exception_handler(request: Request, exc: DomainException):
    logger.warning(f"DomainException en {request.url}: {exc.message}")
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