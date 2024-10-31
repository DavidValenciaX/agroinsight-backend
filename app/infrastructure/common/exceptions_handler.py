from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback
from app.infrastructure.common.common_exceptions import DomainException, UserStateException
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

CUSTOM_MESSAGES = {
    # Errores existentes
    'missing': 'El campo es requerido',
    'value_error.missing': 'El campo es requerido',
    'int_parsing': 'La entrada debe ser un número entero válido',
    'json_invalid': 'Error de decodificación de json',
    'less_than_equal': 'La entrada debe ser menor o igual a {le}',
    'less_than': 'La entrada debe ser menor a {lt}',
    'greater_than_equal': 'La entrada debe ser mayor o igual a {ge}',
    'greater_than': 'La entrada debe ser mayor a {gt}',
    'min_length': 'La entrada debe tener al menos {min_length} caracteres',
    'max_length': 'La entrada debe tener como máximo {max_length} caracteres',
    'decimal_parsing': 'La entrada debe ser un número decimal válido',
    'string_type': 'El valor debe ser una cadena de texto',
    
    # Validaciones de tipos básicos
    'type_error': 'Tipo de dato inválido',
    'type_error.integer': 'El valor debe ser un número entero',
    'type_error.float': 'El valor debe ser un número decimal',
    'type_error.str': 'El valor debe ser una cadena de texto',
    'type_error.bool': 'El valor debe ser verdadero o falso',
    'type_error.list': 'El valor debe ser una lista',
    'type_error.dict': 'El valor debe ser un objeto',
    
    # Validaciones de strings
    'string_pattern_mismatch': 'El valor no coincide con el patrón requerido',
    'string_too_short': 'La cadena debe tener al menos {min_length} caracteres',
    'string_too_long': 'La cadena no debe tener más de {max_length} caracteres',
    'string_contains': 'La cadena debe contener "{pattern}"',
    'string_starts_with': 'La cadena debe comenzar con "{pattern}"',
    'string_ends_with': 'La cadena debe terminar con "{pattern}"',
    
    # Validaciones numéricas
    'number.not_gt': 'El número debe ser mayor que {gt}',
    'number.not_ge': 'El número debe ser mayor o igual que {ge}',
    'number.not_lt': 'El número debe ser menor que {lt}',
    'number.not_le': 'El número debe ser menor o igual que {le}',
    'number.multiple_of': 'El número debe ser múltiplo de {multiple_of}',
    
    # Validaciones de fecha/hora
    'date_parsing': 'Formato de fecha inválido',
    'time_parsing': 'Formato de hora inválido',
    'datetime_parsing': 'Formato de fecha y hora inválido',
    
    # Validaciones de email
    'value_error.email': 'Email inválido',
    
    # Validaciones de URL
    'value_error.url': 'URL inválida',
    'value_error.url.scheme': 'La URL debe comenzar con {scheme}',
    
    # Validaciones de lista
    'list.min_items': 'La lista debe tener al menos {min_items} elementos',
    'list.max_items': 'La lista no debe tener más de {max_items} elementos',
    'list.unique_items': 'La lista debe contener elementos únicos',
    
    # Validaciones de conjunto
    'set.min_items': 'El conjunto debe tener al menos {min_items} elementos',
    'set.max_items': 'El conjunto no debe tener más de {max_items} elementos',
    
    # Validaciones de diccionario
    'dict.min_items': 'El diccionario debe tener al menos {min_items} elementos',
    'dict.max_items': 'El diccionario no debe tener más de {max_items} elementos',
    
    # Otros errores comunes
    'value_error.const': 'Valor no permitido',
    'value_error.regex': 'El valor no coincide con el patrón requerido',
    'value_error.number.not_finite': 'El número debe ser finito',
    'value_error.number.not_multiple_of': 'El número debe ser múltiplo de {multiple_of}',
    'value_error.uuid': 'UUID inválido',
    'value_error.ip_v4': 'Dirección IPv4 inválida',
    'value_error.ip_v6': 'Dirección IPv6 inválida',
}

def convert_errors(errors: List[Dict], custom_messages: Dict[str, str]) -> List[Dict]:
    """
    Convierte una lista de errores utilizando mensajes personalizados.

    Args:
        errors (List[Dict]): Lista de errores a convertir.
        custom_messages (Dict[str, str]): Diccionario de mensajes personalizados.

    Returns:
        List[Dict]: Lista de errores convertidos con mensajes personalizados.
    """
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
    """
    Maneja excepciones de validación y devuelve una respuesta JSON.

    Args:
        request (Request): Objeto de solicitud de FastAPI.
        exc (RequestValidationError): Excepción de validación.

    Returns:
        JSONResponse: Respuesta JSON con detalles de los errores de validación.
    """
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
            "message": [error["msg"].split('\n')] if isinstance(error["msg"], str) else error["msg"]
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
    """
    Maneja excepciones personalizadas y devuelve una respuesta JSON.

    Args:
        request (Request): Objeto de solicitud de FastAPI.
        exc (Exception): Excepción que se ha producido.

    Returns:
        JSONResponse: Respuesta JSON con detalles de la excepción.
    """
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
    """
    Maneja excepciones HTTP y devuelve una respuesta JSON.

    Args:
        request (Request): Objeto de solicitud de FastAPI.
        exc (HTTPException): Excepción HTTP que se ha producido.

    Returns:
        JSONResponse: Respuesta JSON con detalles de la excepción HTTP.
    """
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
    """
    Maneja excepciones de dominio y devuelve una respuesta JSON.

    Args:
        request (Request): Objeto de solicitud de FastAPI.
        exc (DomainException): Excepción de dominio que se ha producido.

    Returns:
        JSONResponse: Respuesta JSON con detalles de la excepción de dominio.
    """
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
    """
    Maneja excepciones relacionadas con el estado del usuario y devuelve una respuesta JSON.

    Args:
        request (Request): Objeto de solicitud de FastAPI.
        exc (UserStateException): Excepción relacionada con el estado del usuario.

    Returns:
        JSONResponse: Respuesta JSON con detalles de la excepción del estado del usuario.
    """
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
