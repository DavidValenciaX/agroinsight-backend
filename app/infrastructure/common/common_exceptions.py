from fastapi import status

class DomainException(Exception):
    def __init__(self, message: str = "Error", status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class UserStateException(Exception):
    def __init__(self, message: str, status_code: int, user_state: str):
        self.message = message
        self.status_code = status_code
        self.user_state = user_state
        super().__init__(self.message)
        
class UserNotRegisteredException(DomainException):
    def __init__(self):
        super().__init__("La cuenta con este email no está registrada", status.HTTP_401_UNAUTHORIZED)
        
class InsufficientPermissionsException(DomainException):
    def __init__(self):
        super().__init__("No tienes permisos para realizar esta acción.", status.HTTP_403_FORBIDDEN)
        
class UserAlreadyRegisteredException(DomainException):
    def __init__(self):
        super().__init__("La cuenta con este email ya está registrada", status.HTTP_409_CONFLICT)
        
class UserHasBeenBlockedException(DomainException):
    def __init__(self, block_time: int):
        super().__init__(f"La cuenta ha sido bloqueada debido a múltiples intentos fallidos. Intente nuevamente en {block_time} minutos.", status.HTTP_429_TOO_MANY_REQUESTS)
        
class MissingTokenException(DomainException):
    def __init__(self):
        super().__init__("Se requiere un token de autenticación", status.HTTP_401_UNAUTHORIZED)