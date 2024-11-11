from sqlalchemy.orm import Session
from app.image_analysis.infrastructure.orm_models import MonitoreoFitosanitario, FallArmywormDetection, DetectionResultEnum
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.application.services.task_service import TaskService
from app.plot.infrastructure.sql_repository import PlotRepository
from app.farm.application.services.farm_service import FarmService
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status, UploadFile
from app.infrastructure.common.datetime_utils import datetime_utc_time
from app.image_analysis.application.cloudinary_service import CloudinaryService
from dotenv import load_dotenv
import os

load_dotenv(override=True)

class DetectFallArmywormUseCase:
    """Caso de uso para procesar detecciones de gusano cogollero"""

    def __init__(self, db: Session):
        self.db = db
        self.cultural_practices_repository = CulturalPracticesRepository(db)
        self.farm_service = FarmService(db)
        self.plot_repository = PlotRepository(db)
        self.cloudinary_service = CloudinaryService()
        self.task_service = TaskService(db)
        self._environment = os.getenv('RAILWAY_ENVIRONMENT_NAME', 'development')

    async def process_detection(self, detection_results: dict, files: list[UploadFile], task_id: int, observations: str, current_user: UserInDB):
        """
        Procesa los resultados de la detección y los guarda en la base de datos
        
        Args:
            detection_results: Resultados del servicio de detección
            files: Archivos de imagen subidos
            task_id: ID de la tarea de monitoreo fitosanitario
            observations: Observaciones generales
            current_user: Usuario actual
            
        Returns:
            dict: Resultados procesados
        """
        # Validar que la tarea existe y el usuario tiene acceso
        task = self.cultural_practices_repository.get_task_by_id(task_id)
        if not task:
            raise DomainException(
                message="La tarea especificada no existe",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Validar que la tarea es de tipo monitoreo fitosanitario
        task_type = self.cultural_practices_repository.get_task_type_by_id(task.tipo_labor_id)
        if not task_type or task_type.nombre != TaskService.MONITOREO_FITOSANITARIO:
            raise DomainException(
                message="La tarea debe ser de tipo 'Monitoreo fitosanitario'",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        lote = self.plot_repository.get_plot_by_id(task.lote_id)
        if not lote:
            raise DomainException(
                message="El lote especificado no existe",
                status_code=status.HTTP_404_NOT_FOUND
            )
                
        # Verificar que el usuario tenga acceso a la tarea
        if not self.farm_service.user_is_farm_admin(current_user.id, lote.finca_id):
            raise DomainException(
                message="No tienes permisos para realizar detecciones en esta tarea",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Crear monitoreo fitosanitario
        monitoreo = MonitoreoFitosanitario(
            tarea_labor_id=task_id,
            fecha_monitoreo=datetime_utc_time(),
            observaciones=observations
        )
        self.db.add(monitoreo)
        self.db.flush()

        # Procesar cada detección individual
        for index, result in enumerate(detection_results["results"]):
            if result["status"] == "success":
                # Generar ruta incluyendo el entorno
                image_folder = f"{self._environment}/fall_armyworm/task_{task_id}"
                
                # Subir imagen a Cloudinary
                cloudinary_result = await self.cloudinary_service.upload_image(
                    files[index],
                    image_folder
                )

                detection = FallArmywormDetection(
                    monitoreo_fitosanitario_id=monitoreo.id,
                    imagen_url=cloudinary_result["url"],
                    imagen_public_id=cloudinary_result["public_id"],
                    resultado_deteccion=DetectionResultEnum[result["predicted_class"]],
                    confianza_deteccion=result["confidence"],
                    prob_leaf_with_larva=result["probabilities"]["leaf_with_larva"],
                    prob_healthy_leaf=result["probabilities"]["healthy_leaf"],
                    prob_damaged_leaf=result["probabilities"]["damaged_leaf"]
                )
                self.db.add(detection)

        try:
            self.db.commit()
            return detection_results
        except Exception as e:
            self.db.rollback()
            raise DomainException(
                message=f"Error guardando los resultados: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 