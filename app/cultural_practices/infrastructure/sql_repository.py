from typing import List
from sqlalchemy.orm import Session
from app.cultural_practices.domain.schemas import AssignmentCreate, TareaLaborCulturalCreate
from app.cultural_practices.infrastructure.orm_models import Asignacion, EstadoTareaLaborCultural, TipoLaborCultural
from app.user.infrastructure.orm_models import User
from app.plot.infrastructure.orm_models import Plot
from app.cultural_practices.infrastructure.orm_models import TareaLaborCultural
from datetime import datetime, timezone

class CulturalPracticesRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def tipo_labor_cultural_exists(self, tipo_labor_id: int) -> bool:
        return self.db.query(TipoLaborCultural).filter(TipoLaborCultural.id == tipo_labor_id).first() is not None

    def estado_tarea_exists(self, estado_id: int) -> bool:
        return self.db.query(EstadoTareaLaborCultural).filter(EstadoTareaLaborCultural.id == estado_id).first() is not None

    def get_estado_tarea_nombre(self, estado_id: int) -> str:
        estado = self.db.query(EstadoTareaLaborCultural).filter(EstadoTareaLaborCultural.id == estado_id).first()
        return estado.nombre if estado else None

    def create_tarea(self, tarea_data: TareaLaborCulturalCreate) -> TareaLaborCultural:
        db_tarea = TareaLaborCultural(**tarea_data.model_dump())
        self.db.add(db_tarea)
        self.db.commit()
        self.db.refresh(db_tarea)
        return db_tarea

    def create_assignment(self, assignment_data: AssignmentCreate) -> Asignacion:
        new_assignment = Asignacion(**assignment_data.model_dump())
        self.db.add(new_assignment)
        self.db.commit()
        self.db.refresh(new_assignment)
        return new_assignment

    def user_exists(self, user_id: int) -> bool:
        return self.db.query(User).filter(User.id == user_id).first() is not None

    def task_exists(self, task_id: int) -> bool:
        return self.db.query(TareaLaborCultural).filter(TareaLaborCultural.id == task_id).first() is not None

    def plot_exists(self, plot_id: int) -> bool:
        return self.db.query(Plot).filter(Plot.id == plot_id).first() is not None

    def get_current_date(self) -> datetime.date:
        return datetime.now(timezone.utc).date()
    
    def list_assignments_by_user_paginated(self, user_id: int, page: int, per_page: int) -> tuple[int, List[Asignacion]]:
        query = self.db.query(Asignacion).filter(Asignacion.usuario_id == user_id)
        total_assignments = query.count()
        assignments = query.offset((page - 1) * per_page).limit(per_page).all()
        return total_assignments, assignments