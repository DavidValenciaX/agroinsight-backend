from functools import wraps
from typing import Optional, Dict, Any
from fastapi import Request
from app.logs.domain.schemas import LogSeverity
from app.logs.application.services.log_service import LogService

def log_activity(
    action_type: str,
    table_name: str,
    severity: LogSeverity = LogSeverity.INFO,
    description: Optional[str] = None
):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Obtener el request y log_service de los kwargs
            request: Request = next((arg for arg in args if isinstance(arg, Request)), 
                                 kwargs.get('request'))
            log_service: LogService = getattr(request.state, 'log_service', None)

            if not log_service:
                # Si no hay log_service, continuar sin logging
                return await func(*args, **kwargs)

            try:
                # Intentar obtener el usuario autenticado
                user = kwargs.get('current_user')
                
                # Si no hay usuario autenticado, intentar obtener el email
                if user is None and 'email' in kwargs:
                    user = kwargs['email']  # Usar el email como identificador
                
                # Ejecutar la función original
                result = await func(*args, **kwargs)

                # Registrar la actividad
                log_service.log_activity(
                    user=user,
                    action_type=action_type,
                    table_name=table_name,
                    request=request,
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