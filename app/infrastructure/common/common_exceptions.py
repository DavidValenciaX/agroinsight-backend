from fastapi import status

class DomainException(Exception):
    """
    Excepción base para errores de dominio.

    Args:
        message (str): Mensaje de error.
        status_code (int): Código de estado HTTP asociado al error.
    """
    def __init__(self, message: str = "Error", status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class UserStateException(Exception):
    """
    Excepción para errores relacionados con el estado del usuario.

    Args:
        message (str): Mensaje de error.
        status_code (int): Código de estado HTTP asociado al error.
        user_state (str): Estado del usuario que causó la excepción.
    """
    def __init__(self, message: str, status_code: int, user_state: str):
        self.message = message
        self.status_code = status_code
        self.user_state = user_state
        super().__init__(self.message)
        
class UserNotRegisteredException(DomainException):
    """
    Excepción lanzada cuando un usuario no está registrado.
    """
    def __init__(self):
        super().__init__("La cuenta no está registrada", status.HTTP_401_UNAUTHORIZED)
        
class InsufficientPermissionsException(DomainException):
    """
    Excepción lanzada cuando un usuario no tiene permisos suficientes.
    """
    def __init__(self):
        super().__init__("No tienes permisos para realizar esta acción.", status.HTTP_403_FORBIDDEN)
        
class UserAlreadyRegisteredException(DomainException):
    """
    Excepción lanzada cuando un usuario ya está registrado.
    """
    def __init__(self):
        super().__init__("La cuenta con este email ya está registrada", status.HTTP_409_CONFLICT)
        
class UserHasBeenBlockedException(DomainException):
    """
    Excepción lanzada cuando un usuario ha sido bloqueado.

    Args:
        block_time (int): Tiempo en minutos hasta que el usuario puede intentar nuevamente.
    """
    def __init__(self, block_time: int):
        super().__init__(f"La cuenta ha sido bloqueada debido a múltiples intentos fallidos. Intente nuevamente en {block_time} minutos.", status.HTTP_429_TOO_MANY_REQUESTS)