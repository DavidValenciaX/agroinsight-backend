from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.orm_models import CulturalTaskState
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository


class TaskService:
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
    
    def __init__(self, db: Session):
        self.db = db
        self.cultural_practices_repository = CulturalPracticesRepository(db)
        
    def get_task_state_by_name(self, estado_nombre: str) -> CulturalTaskState:
        return self.cultural_practices_repository.get_task_state_by_name(estado_nombre)
