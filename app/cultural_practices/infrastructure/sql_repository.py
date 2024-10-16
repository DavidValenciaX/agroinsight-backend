from typing import List
from sqlalchemy.orm import Session
from app.cultural_practices.domain.schemas import AssignmentCreate, TaskCreate
from app.cultural_practices.infrastructure.orm_models import Assignment, CulturalTaskState, CulturalTaskType
from app.cultural_practices.infrastructure.orm_models import CulturalTask
from app.plot.infrastructure.orm_models import Plot

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
FINALIZADA = 'Finalizada'

class CulturalPracticesRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_task_type_by_id(self, tipo_labor_id: int) -> CulturalTaskType:
        return self.db.query(CulturalTaskType).filter(CulturalTaskType.id == tipo_labor_id).first()
    
    def get_task_type_by_name(self, tipo_labor_nombre: str) -> CulturalTaskType:
        return self.db.query(CulturalTaskType).filter(CulturalTaskType.nombre == tipo_labor_nombre).first()
    
    def get_task_state_by_id(self, estado_id: int) -> CulturalTaskState:
        return self.db.query(CulturalTaskState).filter(CulturalTaskState.id == estado_id).first()
    
    def get_task_state_by_name(self, estado_nombre: str) -> CulturalTaskState:
        return self.db.query(CulturalTaskState).filter(CulturalTaskState.nombre == estado_nombre).first()
    
    def get_task_by_id(self, task_id: int) -> CulturalTask:
        return self.db.query(CulturalTask).filter(CulturalTask.id == task_id).first()

    def get_task_state_name(self, estado_id: int) -> str:
        estado = self.db.query(CulturalTaskState).filter(CulturalTaskState.id == estado_id).first()
        return estado.nombre if estado else None
    
    def get_states(self) -> List[CulturalTaskState]:
        return self.db.query(CulturalTaskState).all()

    def create_task(self, tarea_data: TaskCreate) -> CulturalTask:
        try:
            db_tarea = CulturalTask(**tarea_data.model_dump())
            self.db.add(db_tarea)
            self.db.commit()
            self.db.refresh(db_tarea)
            return db_tarea
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear la tarea: {e}")
            return None

    def create_assignment(self, assignment_data: AssignmentCreate) -> Assignment:
        try:
            new_assignment = Assignment(**assignment_data.model_dump())
            self.db.add(new_assignment)
            self.db.commit()
            self.db.refresh(new_assignment)
            return new_assignment
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear la asignación: {e}")
            return None
    
    def list_assignments_by_user_paginated(self, user_id: int, page: int, per_page: int, admin_farm_ids: List[int]) -> tuple[int, List[Assignment]]:
        try:
            query = self.db.query(Assignment).join(CulturalTask).filter(
                Assignment.usuario_id == user_id,
                CulturalTask.lote_id.in_(
                    self.db.query(Plot.id).filter(Plot.finca_id.in_(admin_farm_ids))
                )
            )
            total_assignments = query.count()
            assignments = query.offset((page - 1) * per_page).limit(per_page).all()
            return total_assignments, assignments
        except Exception as e:
            print(f"Error al listar las asignaciones: {e}")
            return 0, []
    
    def get_plot_id_by_task_id(self, tarea_id: int) -> int:
        result = self.db.query(CulturalTask.lote_id).filter(CulturalTask.id == tarea_id).first()
        return result[0] if result else None
    
    def user_has_assignment(self, user_id: int, tarea_id: int) -> bool:
        return self.db.query(Assignment).filter(
            Assignment.usuario_id == user_id, 
            Assignment.tarea_labor_cultural_id == tarea_id
        ).first() is not None

    def list_tasks_by_user_paginated(self, user_id: int, page: int, per_page: int) -> tuple[int, List[CulturalTask]]:
        try:
            query = self.db.query(CulturalTask).join(Assignment).filter(
                Assignment.usuario_id == user_id
            )
            total_tasks = query.count()
            tasks = query.offset((page - 1) * per_page).limit(per_page).all()
            return total_tasks, tasks
        except Exception as e:
            print(f"Error al listar las tareas: {e}")
            return 0, []
        
    def list_tasks_by_user_and_farm_paginated(self, user_id: int, farm_id: int, page: int, per_page: int) -> tuple[int, List[CulturalTask]]:
        try:
            query = self.db.query(CulturalTask).join(Assignment).filter(
                Assignment.usuario_id == user_id,
                CulturalTask.lote_id.in_(self.db.query(Plot.id).filter(Plot.finca_id == farm_id))
            )
            total_tasks = query.count()
            tasks = query.offset((page - 1) * per_page).limit(per_page).all()
            return total_tasks, tasks
        except Exception as e:
            print(f"Error al listar las tareas: {e}")
            return 0, []