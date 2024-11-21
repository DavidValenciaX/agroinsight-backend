from functools import wraps
from typing import Optional
from fastapi import Request, HTTPException, status
from app.infrastructure.common.common_exceptions import DomainException, UserStateException
from app.logs.domain.schemas import LogSeverity
from app.logs.application.services.log_service import LogService
from sqlalchemy.exc import SQLAlchemyError

def _determine_error_severity(error: Exception) -> LogSeverity:
    """Determina la severidad del log basado en el tipo de error."""
    
    # Errores críticos que podrían afectar el funcionamiento del sistema
    if isinstance(error, (
        SQLAlchemyError,  # Errores de base de datos
        ConnectionError,   # Errores de conexión
        MemoryError,      # Errores de memoria
        SystemError       # Errores del sistema
    )):
        return LogSeverity.CRITICAL
    
    # Errores HTTP
    if isinstance(error, (
        HTTPException,
        DomainException,
        UserStateException
    )):
        if error.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            return LogSeverity.CRITICAL
        elif error.status_code >= status.HTTP_400_BAD_REQUEST:
            # 401, 403 -> WARNING
            if error.status_code in [status.HTTP_401_UNAUTHORIZED, 
                                   status.HTTP_403_FORBIDDEN]:
                return LogSeverity.WARNING
            # 400, 404, etc -> ERROR
            return LogSeverity.ERROR
    
    # Por defecto, cualquier otra excepción se considera ERROR
    return LogSeverity.ERROR

def log_activity(
    action_type: str,
    table_name: str,
    severity: LogSeverity = LogSeverity.INFO,
    description: Optional[str] = None,
    get_record_id=None,
    get_old_value=None,
    get_new_value=None
):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = next(
                (arg for arg in args if isinstance(arg, Request)),
                kwargs.get('request')
            )
            log_service: LogService = getattr(request.state, 'log_service', None)

            if not log_service:
                return await func(*args, **kwargs)

            try:
                # Intentar obtener el usuario autenticado
                user = kwargs.get('current_user')
                
                # Si no hay usuario autenticado, buscar el email en diferentes lugares
                if user is None:
                    # Buscar en kwargs directamente
                    email = kwargs.get('email')
                    
                    # Buscar en el body del request si es un modelo Pydantic
                    if not email:
                        for arg in args:
                            if hasattr(arg, 'email'):
                                email = getattr(arg, 'email')
                                break
                        for value in kwargs.values():
                            if hasattr(value, 'email'):
                                email = getattr(value, 'email')
                                break
                    
                    if email:
                        user = email

                # Obtener valor anterior antes de ejecutar la función
                old_value = get_old_value(*args, **kwargs) if get_old_value else None

                # Ejecutar la función original y obtener el resultado
                result = await func(*args, **kwargs)

                # Obtener registro_id y valor_nuevo después de la ejecución
                record_id = get_record_id(*args, **kwargs) if get_record_id else None
                new_value = get_new_value(*args, **kwargs) if get_new_value else None

                # Registrar la actividad
                log_service.log_activity(
                    user=user,
                    action_type=action_type,
                    table_name=table_name,
                    request=request,
                    record_id=record_id,
                    old_value=old_value,
                    new_value=new_value,
                    severity=severity,
                    description=description
                )

                return result

            except Exception as e:
                # Determinar la severidad basada en el error
                error_severity = _determine_error_severity(e)
                
                # Crear una descripción más detallada del error
                error_details = (
                    f"Error: {str(e)}\n"
                    f"Tipo: {type(e).__name__}"
                )
                
                if isinstance(e, HTTPException):
                    error_details += f"\nCódigo de estado: {e.status_code}"
                
                if log_service:
                    log_service.log_activity(
                        user=user if 'user' in locals() else None,
                        action_type=f"{action_type}_ERROR",
                        table_name=table_name,
                        request=request,
                        severity=error_severity,  # Usar la severidad determinada
                        description=error_details
                    )
                raise

        return wrapper
    return decorator 