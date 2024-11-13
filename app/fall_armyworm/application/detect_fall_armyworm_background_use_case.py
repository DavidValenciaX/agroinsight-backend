from sqlalchemy.orm import Session
from app.fall_armyworm.infrastructure.orm_models import EstadoMonitoreoEnum
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.application.services.task_service import TaskService
from app.plot.infrastructure.sql_repository import PlotRepository
from app.farm.application.services.farm_service import FarmService
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status, UploadFile
from app.infrastructure.common.datetime_utils import datetime_utc_time
from app.infrastructure.services.cloudinary_service import CloudinaryService
from dotenv import load_dotenv
import os
import httpx
import logging
from app.fall_armyworm.infrastructure.sql_repository import FallArmywormRepository
from app.fall_armyworm.domain.schemas import (
    FallArmywormDetectionResult,
    FileContent,
    MonitoreoFitosanitarioCreate,
    FallArmywormDetectionCreate,
    PredictionServiceResponse
)
from typing import List, Dict
import math
import asyncio
from app.infrastructure.db.connection import SessionLocal
from fastapi import BackgroundTasks

load_dotenv(override=True)

logger = logging.getLogger(__name__)
ARMYWORM_SERVICE_URL = os.getenv('ARMYWORM_SERVICE_URL', 'http://localhost:8080')

class DetectFallArmywormBackgroundUseCase:
    """Caso de uso para procesar detecciones de gusano cogollero"""

    def __init__(self, db: Session):
        self.db = db
        self.cultural_practices_repository = CulturalPracticesRepository(db)
        self.farm_service = FarmService(db)
        self.plot_repository = PlotRepository(db)
        self.cloudinary_service = CloudinaryService()
        self.task_service = TaskService(db)
        self._environment = os.getenv('RAILWAY_ENVIRONMENT_NAME', 'development')
        self.fall_armyworm_repository = FallArmywormRepository(db)

    async def _process_image_batch(
        self,
        batch_files: List[FileContent],
        task_id: int,
        monitoreo_id: int,
        batch_num: int,
        total_batches: int
    ):
        """
        Procesa un lote de imágenes y crea las detecciones correspondientes
        """
        try:
            # Preparar archivos para el servicio de predicción
            files_to_upload = [
                ("files", (file.filename, file.content, file.content_type))
                for file in batch_files
            ]

            # Obtener predicciones para el lote actual
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(60.0),
                verify=False,
                follow_redirects=True,
                transport=httpx.AsyncHTTPTransport(retries=3)
            ) as client:
                response = await client.post(
                    f"{ARMYWORM_SERVICE_URL}/fall-armyworm/predict",
                    files=files_to_upload
                )

            if response.status_code not in [200, 207]:
                logger.error(f"Error en lote {batch_num + 1}: Status code {response.status_code}")
                return

            detection_results = PredictionServiceResponse(**response.json())

            # Procesar cada detección del lote
            for index, result in enumerate(detection_results.results):
                if result.status == "success":
                    image_folder = f"{self._environment}/fall_armyworm/task_{task_id}"
                    
                    # Subir imagen a Cloudinary
                    cloudinary_result = await self.cloudinary_service.upload_bytes(
                        batch_files[index].content,
                        batch_files[index].filename,
                        image_folder
                    )
                    
                    # Crear detección individual
                    self.fall_armyworm_repository.create_detection(
                        FallArmywormDetectionCreate(
                            monitoreo_fitosanitario_id=monitoreo_id,
                            imagen_url=cloudinary_result["url"],
                            imagen_public_id=cloudinary_result["public_id"],
                            resultado_deteccion=result.predicted_class,
                            confianza_deteccion=result.confidence,
                            prob_leaf_with_larva=result.probabilities.leaf_with_larva,
                            prob_healthy_leaf=result.probabilities.healthy_leaf,
                            prob_damaged_leaf=result.probabilities.damaged_leaf
                        )
                    )

            # Guardar cambios después de cada lote
            self.fall_armyworm_repository.save_changes()

        except Exception as e:
            logger.error(f"Error procesando lote {batch_num + 1}/{total_batches}: {str(e)}")
            
    async def _process_batches(
        self,
        files_content: List[FileContent],
        task_id: int,
        monitoreo_id: int
    ):
        """
        Procesa todos los lotes de imágenes
        """
        try:
            batch_size = 15
            total_batches = math.ceil(len(files_content) / batch_size)

            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min((batch_num + 1) * batch_size, len(files_content))
                batch_files = files_content[start_idx:end_idx]

                await self._process_image_batch(
                    batch_files,
                    task_id,
                    monitoreo_id,
                    batch_num,
                    total_batches
                )

                await asyncio.sleep(1)

            # Actualizar estado del monitoreo al finalizar todos los lotes
            with SessionLocal() as db:
                fall_armyworm_repository = FallArmywormRepository(db)
                monitoreo = fall_armyworm_repository.get_monitoreo_by_id(monitoreo_id)
                if monitoreo:
                    total_detections = len(fall_armyworm_repository.get_detections_by_monitoreo_id(monitoreo_id))
                    if total_detections == 0:
                        monitoreo.estado = EstadoMonitoreoEnum.failed
                    elif total_detections < monitoreo.cantidad_imagenes:
                        monitoreo.estado = EstadoMonitoreoEnum.partial
                    else:
                        monitoreo.estado = EstadoMonitoreoEnum.completed
                    fall_armyworm_repository.save_changes()

        except Exception as e:
            logger.error(f"Error procesando lotes: {str(e)}")
            # Actualizar estado a fallido en caso de error
            with SessionLocal() as db:
                fall_armyworm_repository = FallArmywormRepository(db)
                monitoreo = fall_armyworm_repository.get_monitoreo_by_id(monitoreo_id)
                if monitoreo:
                    monitoreo.estado = EstadoMonitoreoEnum.failed
                    fall_armyworm_repository.save_changes()

    async def process_images_in_background(
        self,
        files_content: List[FileContent],
        task_id: int,
        observations: str,
        user_id: int,
        background_tasks: BackgroundTasks
    ):
        """
        Procesa imágenes en lotes de 15 en segundo plano
        """
        
        """ monitoring_id = await self.create_initial_monitoring(
            task_id=task_id,
            observations=observations,
            total_images=len(files_content)
        ) """
        
        try:
            # Crear una nueva sesión de base de datos
            with SessionLocal() as db:
                # Inicializar los repositorios y servicios con la nueva sesión
                self.db = db
                self.cultural_practices_repository = CulturalPracticesRepository(db)
                self.farm_service = FarmService(db)
                self.plot_repository = PlotRepository(db)
                self.task_service = TaskService(db)
                self.fall_armyworm_repository = FallArmywormRepository(db)

                # Validar acceso y existencia de la tarea
                task = self.cultural_practices_repository.get_task_by_id(task_id)
                if not task:
                    raise DomainException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        message=f"Tarea {task_id} no encontrada"
                    )

                lote = self.plot_repository.get_plot_by_id(task.lote_id)
                if not lote:
                    raise DomainException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        message=f"Lote {task.lote_id} no encontrado"
                    )
                
                if not self.farm_service.user_is_farm_admin(user_id, lote.finca_id):
                    raise DomainException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message=f"Usuario {user_id} sin acceso a tarea {task_id}"
                    )

                # Crear monitoreo fitosanitario principal
                monitoreo = self.fall_armyworm_repository.create_monitoreo(
                    MonitoreoFitosanitarioCreate(
                        tarea_labor_id=task_id,
                        fecha_monitoreo=datetime_utc_time(),
                        observaciones=observations,
                        estado=EstadoMonitoreoEnum.processing,
                        cantidad_imagenes=len(files_content)
                    )
                )

                # Agregar el procesamiento de lotes como tarea en segundo plano
                background_tasks.add_task(
                    self._process_batches,
                    files_content,
                    task_id,
                    monitoreo.id
                )

            return {
                "monitoring_id": monitoreo.id,
                "status": "processing",
                "message": f"Procesando {len(files_content)} imágenes en segundo plano",
                "total_images": len(files_content)
            }

        except Exception as e:
            logger.error(f"Error en proceso background: {str(e)}")
            try:
                with SessionLocal() as db:
                    fall_armyworm_repository = FallArmywormRepository(db)
                    monitoreo = fall_armyworm_repository.get_monitoreo_by_task_id(task_id)
                    if monitoreo:
                        monitoreo.estado = EstadoMonitoreoEnum.failed
                        fall_armyworm_repository.save_changes()
            except Exception as e:
                logger.error(f"Error actualizando estado a failed: {str(e)}")