from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.cultural_practices.application.services.task_service import TaskService
from app.fall_armyworm.domain.schemas import DetectionResult, MonitoreoFitosanitarioResult
from app.fall_armyworm.infrastructure.sql_repository import FallArmywormRepository
from app.farm.application.services.farm_service import FarmService
from app.plot.infrastructure.sql_repository import PlotRepository
from app.user.domain.schemas import UserInDB
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository

class GetMonitoringUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.fall_armyworm_repository = FallArmywormRepository(db)
        self.task_service = TaskService(db)
        self.task_repository = CulturalPracticesRepository(db)
        self.plot_repository = PlotRepository(db)
        self.farm_service = FarmService(db)

    def get_monitoring(self, monitoring_id: int, current_user: UserInDB) -> MonitoreoFitosanitarioResult:

        monitoreo, detections = self.fall_armyworm_repository.get_monitoreo_with_detections(monitoring_id)
        
        if not monitoreo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Monitoreo fitosanitario no encontrado"
            )
            
        # Verificar que el usuario tenga acceso al monitoreo
        task = self.task_repository.get_task_by_id(monitoreo.tarea_labor_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea asociada no encontrada"
            )
            
        plot = self.plot_repository.get_plot_by_id(task.lote_id)
        if not plot:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Lote no encontrado"
            )
            
        if not self.farm_service.user_is_farm_admin(current_user.id, plot.finca_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para ver este monitoreo"
            )
            
        return MonitoreoFitosanitarioResult(
            id=monitoreo.id,
            tarea_labor_id=monitoreo.tarea_labor_id,
            fecha_monitoreo=monitoreo.fecha_monitoreo,
            observaciones=monitoreo.observaciones,
            estado=monitoreo.estado,
            cantidad_imagenes=monitoreo.cantidad_imagenes,
            detecciones=[
                DetectionResult(
                    id=detection.id,
                    imagen_url=detection.imagen_url,
                    resultado_deteccion=detection.resultado_deteccion,
                    confianza_deteccion=detection.confianza_deteccion,
                    prob_leaf_with_larva=detection.prob_leaf_with_larva,
                    prob_healthy_leaf=detection.prob_healthy_leaf,
                    prob_damaged_leaf=detection.prob_damaged_leaf
                )
                for detection in detections
            ]
        )