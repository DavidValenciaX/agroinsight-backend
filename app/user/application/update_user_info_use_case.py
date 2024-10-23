from sqlalchemy.orm import Session
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserInDB, UserUpdate
from app.infrastructure.common.common_exceptions import DomainException, UserAlreadyRegisteredException
from fastapi import status

class UpdateUserInfoUseCase:
    """
    Caso de uso para actualizar la información de un usuario.

    Esta clase maneja el proceso de actualización de la información del usuario,
    incluyendo la verificación de correo electrónico duplicado.

    Attributes:
        db (Session): Sesión de base de datos para operaciones de persistencia.
        user_repository (UserRepository): Repositorio para operaciones relacionadas con usuarios.
    """

    def __init__(self, db: Session):
        """
        Inicializa una nueva instancia de UpdateUserInfoUseCase.

        Args:
            db (Session): Sesión de base de datos para operaciones de persistencia.
        """
        self.db = db
        self.user_repository = UserRepository(db)
        
    def update_user_info(self, current_user: UserInDB, user_update: UserUpdate) -> SuccessResponse:
        """
        Actualiza la información del usuario.

        Este método verifica si el nuevo correo electrónico ya está en uso,
        actualiza la información del usuario y guarda los cambios en la base de datos.

        Args:
            current_user (User): Usuario actual cuya información se va a actualizar.
            user_update (UserUpdate): Datos actualizados del usuario.

        Returns:
            SuccessResponse: Respuesta indicando que la actualización fue exitosa.

        Raises:
            UserAlreadyRegisteredException: Si el nuevo correo electrónico ya está en uso por otro usuario.
            DomainException: Si no se pudo actualizar la información del usuario.
        """
        # Verificar si el email ya está en uso por otro usuario
        if user_update.email != current_user.email:
            if self.user_repository.get_user_by_email(user_update.email):
                raise UserAlreadyRegisteredException()
            
            current_user.email = user_update.email
        
        current_user.nombre = user_update.nombre
        current_user.apellido = user_update.apellido
        
        if not self.user_repository.update_user(current_user):
            raise DomainException(
                message="No se pudo actualizar la información del usuario.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return SuccessResponse(message="Usuario actualizado exitosamente")
