from functools import wraps
from typing import Optional, Dict, Any
from fastapi import Request
from app.logs.domain.schemas import LogSeverity
from app.logs.application.services.log_service import LogService

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
                # Registrar el error si ocurre
                if log_service:
                    log_service.log_activity(
                        user=user if 'user' in locals() else None,
                        action_type=f"{action_type}_ERROR",
                        table_name=table_name,
                        request=request,
                        severity=LogSeverity.ERROR,
                        description=f"Error: {str(e)}"
                    )
                raise

        return wrapper
    return decorator 