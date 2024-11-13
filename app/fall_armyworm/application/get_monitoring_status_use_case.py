from fastapi import status
from sqlalchemy.orm import Session
from app.fall_armyworm.infrastructure.sql_repository import FallArmywormRepository
from app.infrastructure.common.common_exceptions import DomainException     
        
class GetMonitoringStatusUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.fall_armyworm_repository = FallArmywormRepository(db)

    def get_monitoring_status(self, monitoring_id: int) -> dict:

        
        monitoreo = self.fall_armyworm_repository.get_monitoreo_by_id(monitoring_id)
        if not monitoreo:
            raise DomainException(
                message="No se encontró un monitoreo para esta tarea",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        detections = self.fall_armyworm_repository.get_detections_by_monitoreo_id(monitoreo.id)
        
        return {
            "status": monitoreo.estado.value,
            "total_processed": len(detections),
            "monitoring_id": monitoreo.id
        }