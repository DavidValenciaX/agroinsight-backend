"""
Este módulo contiene la implementación del caso de uso para obtener la información del usuario actual.
"""

from sqlalchemy.orm import Session
from app.infrastructure.mappers.response_mappers import map_user_to_response
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.schemas import UserResponse, UserInDB
from app.infrastructure.common.common_exceptions import MissingTokenException, UserStateException
from fastapi import status

class GetCurrentUserUseCase:
    """
    Caso de uso para obtener la información del usuario actual.

    Esta clase maneja la lógica para recuperar y validar la información del usuario actual.

    Attributes:
        db (Session): La sesión de base de datos para realizar operaciones.
        user_repository (UserRepository): Repositorio para operaciones de usuario.
    """

    def __init__(self, db: Session):
        """
        Inicializa una nueva instancia de GetCurrentUserUseCase.

        Args:
            db (Session): La sesión de base de datos a utilizar.
        """
        self.db = db
        self.user_repository = UserRepository(db)
        
    def get_current_user(self, current_user: UserInDB) -> UserResponse:
        """
        Obtiene la información del usuario actual.

        Este método verifica la existencia del usuario actual y su estado,
        y devuelve la información del usuario mapeada a la respuesta adecuada.

        Args:
            current_user (UserInDB): El usuario actual autenticado.

        Returns:
            UserResponse: La información del usuario mapeada a la respuesta.

        Raises:
            MissingTokenException: Si no se proporciona un usuario actual.
            UserStateException: Si el estado del usuario no es reconocido.
        """
        if not current_user:
            raise MissingTokenException()
            
        # Obtener el estado del usuario
        estado = self.user_repository.get_state_by_id(current_user.state_id)
        if not estado:
            raise UserStateException(
                message="Estado de usuario no reconocido.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                user_state="unknown"
            )
        
        current_user.estado = estado
        return map_user_to_response(current_user)
