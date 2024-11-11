from sqlalchemy.orm import Session
from app.image_analysis.infrastructure.orm_models import MonitoreoFitosanitario, FallArmywormDetection
from app.image_analysis.domain.schemas import MonitoreoFitosanitarioCreate, FallArmywormDetectionCreate

class FallArmywormRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_monitoreo(self, monitoreo_data: MonitoreoFitosanitarioCreate) -> MonitoreoFitosanitario:
        monitoreo = MonitoreoFitosanitario(
            tarea_labor_id=monitoreo_data.tarea_labor_id,
            fecha_monitoreo=monitoreo_data.fecha_monitoreo,
            observaciones=monitoreo_data.observaciones
        )
        self.db.add(monitoreo)
        self.db.flush()
        return monitoreo

    def create_detection(self, detection_data: FallArmywormDetectionCreate) -> FallArmywormDetection:
        detection = FallArmywormDetection(
            monitoreo_fitosanitario_id=detection_data.monitoreo_fitosanitario_id,
            imagen_url=detection_data.imagen_url,
            imagen_public_id=detection_data.imagen_public_id,
            resultado_deteccion=detection_data.resultado_deteccion,
            confianza_deteccion=detection_data.confianza_deteccion,
            prob_leaf_with_larva=detection_data.prob_leaf_with_larva,
            prob_healthy_leaf=detection_data.prob_healthy_leaf,
            prob_damaged_leaf=detection_data.prob_damaged_leaf
        )
        self.db.add(detection)
        return detection

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()