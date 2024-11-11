from typing import List
from sqlalchemy.orm import Session
from app.fall_armyworm.infrastructure.orm_models import MonitoreoFitosanitario, FallArmywormDetection
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from app.fall_armyworm.domain.schemas import MonitoreoFitosanitarioCreate, FallArmywormDetectionCreate

class FallArmywormRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_monitoreo(self, monitoreo_data: MonitoreoFitosanitarioCreate) -> MonitoreoFitosanitario:
        monitoreo = MonitoreoFitosanitario(**monitoreo_data.model_dump())
        self.db.add(monitoreo)
        self.db.flush()
        return monitoreo

    def create_detection(self, detection_data: FallArmywormDetectionCreate) -> FallArmywormDetection:
        detection = FallArmywormDetection(**detection_data.model_dump())
        self.db.add(detection)
        return detection

    def save_changes(self):
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise DomainException(
                message=f"Error guardando los resultados: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    def get_monitoreo_by_task_id(self, task_id: int) -> MonitoreoFitosanitario:
        return self.db.query(MonitoreoFitosanitario)\
            .filter(MonitoreoFitosanitario.tarea_labor_id == task_id)\
            .first()

    def get_detections_by_monitoreo_id(self, monitoreo_id: int) -> List[FallArmywormDetection]:
        return self.db.query(FallArmywormDetection)\
            .filter(FallArmywormDetection.monitoreo_fitosanitario_id == monitoreo_id)\
            .all()