from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.orm_models import CulturalTaskState
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository


class TaskService:
    """Servicio para gestionar la lógica de negocio relacionada con las tareas de labor cultural.

    Este servicio proporciona constantes para los diferentes estados de las tareas y gestiona
    las operaciones relacionadas con las tareas a través del repositorio de prácticas culturales.

    Attributes:
        PROGRAMADA (str): Estado de la tarea programada.
        EN_PROGRESO (str): Estado de la tarea en progreso.
        COMPLETADA (str): Estado de la tarea completada.
        CANCELADA (str): Estado de la tarea cancelada.
        PENDIENTE (str): Estado de la tarea pendiente.
        RETRASADA (str): Estado de la tarea retrasada.
        FALLIDA (str): Estado de la tarea fallida.
        REVISADA (str): Estado de la tarea revisada.
        APROBADA (str): Estado de la tarea aprobada.
        POSTERGADA (str): Estado de la tarea postergada.
        CERRADA (str): Estado de la tarea cerrada.
        db (Session): Sesión de base de datos SQLAlchemy.
        cultural_practices_repository (CulturalPracticesRepository): Repositorio para operaciones de prácticas culturales.
    """

    PROGRAMADA = 'Programada'
    EN_PROGRESO = 'En Progreso'
    COMPLETADA = 'Completada'
    CANCELADA = 'Cancelada'
    PENDIENTE = 'Pendiente'
    RETRASADA = 'Retrasada'
    FALLIDA = 'Fallida'
    REVISADA = 'Revisada'
    APROBADA = 'Aprobada'
    POSTERGADA = 'Postergada'
    CERRADA = 'Cerrada'
    
    MONITOREO_FITOSANITARIO = 'Monitoreo fitosanitario'
    
    def __init__(self, db: Session):
        """Inicializa el servicio de tareas con la sesión de base de datos.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        self.cultural_practices_repository = CulturalPracticesRepository(db)
