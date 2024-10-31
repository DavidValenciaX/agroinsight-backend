from sqlalchemy.orm import Session
from app.cultural_practices.domain.schemas import TaskTypeListResponse
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository 
from app.infrastructure.mappers.response_mappers import map_task_type_to_response
from app.user.domain.schemas import UserInDB

class ListTaskTypesUseCase:
    """Caso de uso para listar los tipos de tareas de labor cultural.

    Este caso de uso gestiona la lógica de negocio para recuperar todos los tipos de tareas,
    asegurando que se cumplan las validaciones necesarias antes de devolver la lista de tipos.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
        cultural_practice_repository (CulturalPracticesRepository): Repositorio para operaciones de prácticas culturales.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)

    def list_task_types(self, current_user: UserInDB) -> TaskTypeListResponse:
        """Lista todos los tipos de tareas de labor cultural.

        Este método obtiene todos los tipos de tareas desde el repositorio y los mapea a
        objetos de respuesta.

        Args:
            current_user (UserInDB): Usuario actual autenticado que intenta acceder a los tipos de tareas.

        Returns:
            TaskTypeListResponse: Respuesta que contiene la lista de tipos de tareas.
        """
        task_types = self.cultural_practice_repository.get_task_types()
        task_type_responses = [map_task_type_to_response(type) for type in task_types]
        return TaskTypeListResponse(task_types=task_type_responses)

