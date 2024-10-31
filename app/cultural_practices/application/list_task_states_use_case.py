from sqlalchemy.orm import Session
from app.cultural_practices.domain.schemas import TaskStateResponse, TaskStateListResponse
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository 
from app.infrastructure.common.common_exceptions import DomainException
from app.infrastructure.mappers.response_mappers import map_task_state_to_response
from app.user.domain.schemas import UserInDB

class ListTaskStatesUseCase:
    """Caso de uso para listar los estados de las tareas de labor cultural.

    Este caso de uso gestiona la lógica de negocio para recuperar todos los estados de las tareas,
    asegurando que se cumplan las validaciones necesarias antes de devolver la lista de estados.

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

    def list_task_states(self, current_user: UserInDB) -> TaskStateListResponse:
        """Lista todos los estados de las tareas de labor cultural.

        Este método obtiene todos los estados de las tareas desde el repositorio y los mapea a
        objetos de respuesta. Si ocurre un error durante la obtención, se lanza una excepción.

        Args:
            current_user (UserInDB): Usuario actual autenticado que intenta acceder a los estados.

        Returns:
            TaskStateListResponse: Respuesta que contiene la lista de estados de las tareas.

        Raises:
            DomainException: Si ocurre un error al obtener los estados de las tareas.
        """
        try:
            # Asumiendo que el método del repositorio devuelve una lista de objetos de estado de tarea
            task_states = self.cultural_practice_repository.get_states()
            
            # Crear objetos TaskStateResponse
            task_state_responses = [map_task_state_to_response(state) for state in task_states]
            
            # Retornar un objeto TaskStateListResponse
            return TaskStateListResponse(states=task_state_responses)
        except Exception as e:
            raise DomainException(f"Error obteniendo los estados de las tareas: {str(e)}")
