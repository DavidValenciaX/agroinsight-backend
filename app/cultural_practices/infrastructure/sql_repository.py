from sqlalchemy.orm import Session
from app.cultural_practices.domain.schemas import AssignmentCreate
from app.cultural_practices.infrastructure.orm_models import Asignacion
from app.user.infrastructure.orm_models import User
from app.plot.infrastructure.orm_models import Plot
from app.cultural_practices.infrastructure.orm_models import TareaLaborCultural

class AssignmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_assignment(self, assignment_data: AssignmentCreate) -> Asignacion:
        new_assignment = Asignacion(**assignment_data.dict())
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