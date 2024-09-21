class DomainException(Exception):
    def __init__(self, message: str = "Error", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class TooManyRecoveryAttempts(DomainException):
    """Excepción lanzada cuando un usuario excede los intentos de confirmación de recuperación permitidos."""
    def __init__(self, message: str = "Demasiados intentos. Inténtalo de nuevo en 10 minutos.", status_code: int = 403):
        super().__init__(message, status_code)