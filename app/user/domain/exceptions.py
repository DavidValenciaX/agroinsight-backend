class DomainException(Exception):
    def __init__(self, message: str = "Error", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class TooManyConfirmationAttempts(DomainException):
    """Excepción lanzada cuando un usuario excede los intentos de confirmación permitidos."""
    def __init__(self, message: str = "Demasiados intentos fallidos. Intenta crear tu cuenta nuevamente desde el inicio.", status_code: int = 403):
        super().__init__(message, status_code)

class TooManyRecoveryAttempts(DomainException):
    """Excepción lanzada cuando un usuario excede los intentos de confirmación de recuperación permitidos."""
    def __init__(self, message: str = "Demasiados intentos. Inténtalo de nuevo en 10 minutos.", status_code: int = 403):
        super().__init__(message, status_code)

class UserAlreadyExistsException(DomainException):
    """Excepción lanzada cuando un usuario ya existe y no tiene una confirmación pendiente."""
    def __init__(self, message: str = "El usuario ya existe.", status_code: int = 400):
        super().__init__(message, status_code)

class ConfirmationError(DomainException):
    """Excepción lanzada cuando falla la creación de la confirmación o el envío del email."""
    def __init__(self, message: str = "Error al procesar la confirmación.", status_code: int = 500):
        super().__init__(message, status_code)