
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