from sqlalchemy.orm import Session
from app.image_analysis.infrastructure.orm_models import MonitoreoFitosanitario, FallArmywormDetection
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from app.image_analysis.domain.schemas import MonitoreoFitosanitarioCreate, FallArmywormDetectionCreate

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