from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback
from app.infrastructure.common.common_exceptions import DomainException, UserStateException
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

CUSTOM_MESSAGES = {
    'missing': 'El campo es requerido',
    'value_error.missing': 'El campo es requerido',
    'int_parsing': 'La entrada debe ser un número entero válido',
    'json_invalid': 'Error de decodificación de json',
    'less_than_equal': 'La entrada debe ser menor o igual a {le}',
    'less_than': 'La entrada debe ser menor a {lt}',
    'greater_than_equal': 'La entrada debe ser mayor o igual a {ge}',
    'greater_than': 'La entrada debe ser mayor a {gt}',
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
    errors = convert_errors(errors, CUSTOM_MESSAGES)
    error_details = []
    
    logger.info(f"Raw validation errors: {errors}")
    
    for error in errors:
        logger.info(f"Processing error: {error}")
        logger.info(f"Error type: {error.get('type')}")
        logger.info(f"Error message: {error.get('msg')}")
        
        # Procesamiento especial para errores de validación de email
        if error.get("type") == "value_error" and isinstance(error.get("msg"), str):
            try:
                error_msg = error['msg']
                # Remover el prefijo "Value error, " si existe
                if error_msg.startswith("Value error, "):
                    error_msg = error_msg[len("Value error, "):]
                
                logger.info(f"Cleaned error message: {error_msg}")
                
                # Verificar si es una lista de errores
                if error_msg.startswith('[') and error_msg.endswith(']'):
                    # Convertir string a lista usando ast.literal_eval (más seguro que eval)
                    import ast
                    error_list = ast.literal_eval(error_msg)
                    logger.info(f"Parsed error list: {error_list}")
                    
                    for email_error in error_list:
                        error_details.append({
                            "field": "user_emails",
                            "type": "email_validation",
                            "message": [email_error]
                        })
                    continue
            except Exception as e:
                logger.error(f"Error parsing message: {str(e)}")
                logger.error(f"Original message: {error['msg']}")
                
        # Procesamiento normal para otros tipos de errores
        error_detail = {
            "field": error.get("loc", [""])[1] if len(error.get("loc", [])) > 1 else error.get("loc", [""])[0],
            "type": error.get("type", ""),
            "message": [error["msg"]] if isinstance(error["msg"], str) else error["msg"]
        }
        error_details.append(error_detail)

    error_response = {
        "error": {
            "route": str(request.url),
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "message": "Error en la validación de los datos de entrada",
            "details": error_details
        }
    }
    
    logger.info(f"Final error response: {error_response}")

    return JSONResponse(
        status_code=422,
        content=error_response
    )

def custom_exception_handler(request: Request, exc: Exception):
    error_details = {
        "message": str(exc),
        "type": type(exc).__name__,
        "traceback": traceback.format_exc()
    }
    logger.error(f"Excepción no controlada en {request.url}: {error_details}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "route": str(request.url),
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error interno del servidor",
                "details": [error_details]
            }
        },
    )

def custom_http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTPException en {request.url}: status_code={exc.status_code}, message='{exc.detail}'")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "route": str(request.url),
                "status_code": exc.status_code,
                "message": exc.detail
            }
        },
    )
    
def domain_exception_handler(request: Request, exc: DomainException):
    error_response = {
        "error": {
            "route": str(request.url),
            "status_code": exc.status_code,
            "message": exc.message
        }
    }
    logger.error(f"Domain exception en {request.url}: status_code={exc.status_code}, message='{exc.message}'")
    return JSONResponse(status_code=exc.status_code, content=error_response)
    
def user_state_exception_handler(request: Request, exc: UserStateException):
    logger.warning(f"UserStateException in {request.url}: status_code={exc.status_code}, message='{exc.message}', user_state='{exc.user_state}'")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "route": str(request.url),
                "status_code": exc.status_code,
                "message": exc.message,
                "user_state": exc.user_state
            }
        }
    )
