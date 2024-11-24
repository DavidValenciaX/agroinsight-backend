from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository


class TaskService:
    """Servicio para gestionar la lógica de negocio relacionada con las tareas de labor cultural.

    Este servicio proporciona constantes para los diferentes estados de las tareas y gestiona
    las operaciones relacionadas con las tareas a través del repositorio de prácticas culturales.

    Attributes:
        PENDIENTE (str): Estado de la tarea pendiente.
        EN_PROGRESO (str): Estado de la tarea en progreso.
        COMPLETADA (str): Estado de la tarea completada.
        
        db (Session): Sesión de base de datos SQLAlchemy.
        cultural_practices_repository (CulturalPracticesRepository): Repositorio para operaciones de prácticas culturales.
    """

    PENDIENTE = 'Pendiente'
    EN_PROGRESO = 'En Progreso'
    COMPLETADA = 'Completada'
    
    # Nuevas constantes para los comandos de texto
    IN_PROGRESS = 'in_progress'
    DONE = 'done'
    
    # Tipos de tareas de lotes
    LABRANZA = 'Labranza'
    ARADO = 'Arado'
    RASTRILLADO = 'Rastrillado'
    COMPACTACION = 'Compactación'
    ANALISIS_SUELO = 'Análisis de suelo'
    ROTACION_DE_CULTIVOS = 'Rotación de cultivos'
    MANEJO_DE_RESIDUOS_AGRICOLA = 'Manejo de residuos agrícolas'
    
    # Tipos de tareas de cultivos
    
    SIEMBRA = 'Siembra'
    FERTILIZACION = 'Fertilización' 
    RIEGO = 'Riego'
    CONTROL_DE_PLAGAS = 'Control de plagas'
    CONTROL_DE_MALEZAS = 'Control de malezas'
    COSECHA = 'Cosecha'
    SECADO = 'Secado'
    LIMPIEZA = 'Limpieza'
    CLASIFICACION_Y_SELECCION = 'Clasificación y selección'
    ALMACENAMIENTO = 'Almacenamiento'
    EMPAQUE = 'Empaque'
    TRANSPORTE = 'Transporte'
    TRATAMIENTO_POST_COSECHA = 'Tratamiento post-cosecha'
    MONITOREO_FITOSANITARIO = 'Monitoreo fitosanitario'
    APLICACION_DE_FUNGICIDAS = 'Aplicación de fungicidas'
    CONTROL_BIOLOGICO_DE_PLAGAS = 'Control biológico de plagas'
    
    def __init__(self, db: Session):
        """Inicializa el servicio de tareas con la sesión de base de datos.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        self.cultural_practices_repository = CulturalPracticesRepository(db)

    def get_state_id_from_command(self, state_command: str) -> int:
        """Convierte un comando de texto en el ID del estado correspondiente.
        
        Args:
            state_command (str): Comando de texto ('in_progress' o 'done').
            
        Returns:
            int: ID del estado correspondiente.
        """
        if state_command == self.IN_PROGRESS:
            return 2  # ID para "En Progreso"
        elif state_command == self.DONE:
            return 3  # ID para "Completada"
        return None
