from sqlalchemy.orm import Session
from app.infrastructure.common.response_models import SuccessResponse
from app.user.infrastructure.orm_models import BlacklistedToken
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class LogoutUseCase:
    """
    Caso de uso para gestionar el cierre de sesión de un usuario.

    Esta clase maneja el proceso de cerrar sesión, incluyendo la inclusión
    del token en la lista negra.

    Attributes:
        user_repository (UserRepository): Repositorio para operaciones relacionadas con usuarios.
    """

    def __init__(self, db: Session):
        """
        Inicializa una nueva instancia de LogoutUseCase.

        Args:
            db (Session): Sesión de base de datos para operaciones de persistencia.
        """
        self.user_repository = UserRepository(db)
    
    def logout(self, token: str, user_id: int) -> SuccessResponse:
        """
        Realiza el proceso de cierre de sesión para un usuario.

        Este método intenta incluir el token en la lista negra y devuelve una respuesta
        de éxito si se logra, o lanza una excepción si falla.

        Args:
            token (str): Token de autenticación a incluir en la lista negra.
            user_id (int): ID del usuario que está cerrando sesión.

        Returns:
            SuccessResponse: Respuesta indicando que el cierre de sesión fue exitoso.

        Raises:
            DomainException: Si no se pudo cerrar la sesión.
        """
        success = self.blacklist_token(token, user_id)
        if not success:
            raise DomainException(
                message="No se pudo cerrar la sesión. Intenta nuevamente.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return SuccessResponse(
                message="Sesión cerrada exitosamente."
        )
        
    def blacklist_token(self, token: str, user_id: int) -> bool:
        """
        Incluye un token en la lista negra.

        Args:
            token (str): Token de autenticación a incluir en la lista negra.
            user_id (int): ID del usuario asociado al token.

        Returns:
            bool: True si el token se incluyó exitosamente en la lista negra, False en caso contrario.
        """
        blacklisted = BlacklistedToken(token=token, usuario_id=user_id)
        return self.user_repository.blacklist_token(blacklisted)
