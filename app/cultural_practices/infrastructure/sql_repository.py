from typing import List
from sqlalchemy.orm import Session
from app.cultural_practices.domain.schemas import AssignmentCreate, TaskCreate
from app.cultural_practices.infrastructure.orm_models import Assignment, CulturalTaskState, CulturalTaskType
from app.cultural_practices.infrastructure.orm_models import CulturalTask
from app.plot.infrastructure.orm_models import Plot

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
    
    def get_states(self) -> List[CulturalTaskState]:
        return self.db.query(CulturalTaskState).all()

    def create_task(self, task_data: TaskCreate) -> CulturalTask:
        try:
            new_task = CulturalTask(
                nombre=task_data.nombre,
                tipo_labor_id=task_data.tipo_labor_id,
                fecha_inicio_estimada=task_data.fecha_inicio_estimada,
                fecha_finalizacion=task_data.fecha_finalizacion,
                descripcion=task_data.descripcion,
                estado_id=task_data.estado_id,
                lote_id=task_data.lote_id
            )
            self.db.add(new_task)
            self.db.commit()
            self.db.refresh(new_task)
            return new_task
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
    
    def get_plot_id_by_task_id(self, tarea_id: int) -> int:
        result = self.db.query(CulturalTask.lote_id).filter(CulturalTask.id == tarea_id).first()
        return result[0] if result else None
    
    def user_has_assignment(self, user_id: int, tarea_id: int) -> bool:
        return self.db.query(Assignment).filter(
            Assignment.usuario_id == user_id, 
            Assignment.tarea_labor_cultural_id == tarea_id
        ).first() is not None
        
    def list_tasks_by_user_and_farm_paginated(self, user_id: int, farm_id: int, page: int, per_page: int) -> tuple[int, List[CulturalTask]]:
        query = self.db.query(CulturalTask).join(Assignment).filter(
            Assignment.usuario_id == user_id,
            CulturalTask.lote_id.in_(self.db.query(Plot.id).filter(Plot.finca_id == farm_id))
        )
        total_tasks = query.count()
        tasks = query.offset((page - 1) * per_page).limit(per_page).all()
        return total_tasks, tasks