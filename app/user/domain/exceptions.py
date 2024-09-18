class TooManyConfirmationAttempts(Exception):
    """Excepción lanzada cuando un usuario excede los intentos de confirmación permitidos."""
    def __init__(self, message: str = "Demasiados intentos fallidos. Intenta crear tu cuenta nuevamente desde el inicio."):
        self.message = message
        super().__init__(self.message)
        
class TooManyRecoveryAttempts(Exception):
    """Excepción lanzada cuando un usuario excede los intentos de confirmación de recuperación permitidos."""
    def __init__(self, message: str = "Demasiados intentos. Inténtalo de nuevo en 10 minutos."):
        self.message = message
        super().__init__(self.message)
        
class UserAlreadyExistsException(Exception):
    """Excepción lanzada cuando un usuario ya existe y no tiene una confirmación pendiente."""
    def __init__(self, message: str = "El usuario ya existe."):
        self.message = message
        super().__init__(self.message)

class ConfirmationError(Exception):
    """Excepción lanzada cuando falla la creación de la confirmación o el envío del email."""
    def __init__(self, message: str = "Error al procesar la confirmación."):
        self.message = message
        super().__init__(self.message)
        
class PasswordValidationError(Exception):
    """Excepción lanzada cuando la validación de la contraseña falla."""
    def __init__(self, errors: list):
        self.errors = errors
        super().__init__(", ".join(errors))