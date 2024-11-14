from sqlalchemy.orm import Session
from app.soil_analysis.domain.schemas import PredictionServiceResponse
from app.soil_analysis.infrastructure.orm_models import SoilAnalysisStatusEnum
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.application.services.task_service import TaskService
from app.plot.infrastructure.sql_repository import PlotRepository
from app.farm.application.services.farm_service import FarmService
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import BackgroundTasks, status, UploadFile
from app.infrastructure.common.datetime_utils import datetime_utc_time
from app.infrastructure.services.cloudinary_service import CloudinaryService
from dotenv import load_dotenv
import os
import httpx
import logging
from app.soil_analysis.infrastructure.sql_repository import SoilAnalysisRepository
from app.soil_analysis.domain.schemas import (
    SoilAnalysisResponse,
    FileContent,
    SoilAnalysisCreate,
    SoilClassificationCreate
)
from typing import List, Dict
import math
import asyncio
from app.infrastructure.db.connection import SessionLocal

load_dotenv(override=True)

logger = logging.getLogger(__name__)
SOIL_ANALYSIS_SERVICE_URL = os.getenv('SOIL_ANALYSIS_SERVICE_URL', 'http://localhost:8080')

class SoilAnalysisBackgroundUseCase:
    """Caso de uso para procesar análisis de suelo en segundo plano"""

    def __init__(self, db: Session):
        self.db = db
        self.cultural_practices_repository = CulturalPracticesRepository(db)
        self.farm_service = FarmService(db)
        self.plot_repository = PlotRepository(db)
        self.cloudinary_service = CloudinaryService()
        self.task_service = TaskService(db)
        self._environment = os.getenv('RAILWAY_ENVIRONMENT_NAME', 'development')
        self.soil_analysis_repository = SoilAnalysisRepository(db)
        
    async def _process_image_batch(
        self,
        batch_files: List[FileContent],
        task_id: int,
        analysis_id: int,
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
                    f"{SOIL_ANALYSIS_SERVICE_URL}/soil-analysis/predict",
                    files=files_to_upload
                )

            if response.status_code not in [200, 207]:
                logger.error(f"Error en lote {batch_num + 1}: Status code {response.status_code}")
                return

            detection_results = PredictionServiceResponse(**response.json())

            # Procesar cada detección del lote
            for index, result in enumerate(detection_results.results):
                if result.status == "success":
                    image_folder = f"{self._environment}/soil_analysis/task_{task_id}"
                    
                    # Subir imagen a Cloudinary
                    cloudinary_result = await self.cloudinary_service.upload_bytes(
                        batch_files[index].content,
                        batch_files[index].filename,
                        image_folder
                    )
                    
                    predicted_class = self.soil_analysis_repository.get_soil_type_by_name(result.predicted_class)
                    
                    # Crear detección individual
                    self.soil_analysis_repository.create_classification(
                        SoilClassificationCreate(
                            analisis_suelo_id=analysis_id,
                            imagen_url=cloudinary_result["url"],
                            imagen_public_id=cloudinary_result["public_id"],
                            resultado_analisis_id=predicted_class.id,
                            confianza_clasificacion=result.confidence,
                            prob_laterite_soil=result.probabilities.laterite_soil,
                            prob_peat_soil=result.probabilities.peat_soil,
                            prob_yellow_soil=result.probabilities.yellow_soil,
                            prob_cinder_soil=result.probabilities.cinder_soil,
                            prob_clay_soil=result.probabilities.clay_soil,
                            prob_black_soil=result.probabilities.black_soil,
                            prob_alluvial_soil=result.probabilities.alluvial_soil
                        )
                    )

            # Guardar cambios después de cada lote
            self.soil_analysis_repository.save_changes()
            
        except Exception as e:
            logger.error(f"Error procesando lote {batch_num + 1}/{total_batches}: {str(e)}")
            
    async def _process_batches(
        self,
        files_content: List[FileContent],
        task_id: int,
        analysis_id: int
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
                    analysis_id,
                    batch_num,
                    total_batches
                )

                await asyncio.sleep(1)

            # Actualizar estado del monitoreo al finalizar todos los lotes
            with SessionLocal() as db:
                soil_analysis_repository = SoilAnalysisRepository(db)
                analysis = soil_analysis_repository.get_analysis_by_id(analysis_id)
                if analysis:
                    total_classifications = len(soil_analysis_repository.get_classifications_by_analysis_id(analysis_id))
                    if total_classifications == 0:
                        analysis.estado = SoilAnalysisStatusEnum.failed
                    elif total_classifications < analysis.cantidad_imagenes:
                        analysis.estado = SoilAnalysisStatusEnum.partial
                    else:
                        analysis.estado = SoilAnalysisStatusEnum.completed
                    soil_analysis_repository.save_changes()
                    
        except Exception as e:
            logger.error(f"Error procesando lotes: {str(e)}")
            # Actualizar estado a fallido en caso de error
            with SessionLocal() as db:
                soil_analysis_repository = SoilAnalysisRepository(db)
                analysis = soil_analysis_repository.get_analysis_by_id(analysis_id)
                if analysis:
                    analysis.estado = SoilAnalysisStatusEnum.failed
                    soil_analysis_repository.save_changes()
    
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
        try:
            # Crear una nueva sesión de base de datos
            db = SessionLocal()
            try:
                # Inicializar los repositorios y servicios con la nueva sesión
                self.db = db
                self.cultural_practices_repository = CulturalPracticesRepository(db)
                self.farm_service = FarmService(db)
                self.plot_repository = PlotRepository(db)
                self.task_service = TaskService(db)
                self.soil_analysis_repository = SoilAnalysisRepository(db)

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
                    
                current_datetime = datetime_utc_time()

                # Crear análisis de suelo principal
                analysis = self.soil_analysis_repository.create_analysis(
                    SoilAnalysisCreate(
                        tarea_labor_id=task_id,
                        fecha_analisis=current_datetime.date(),
                        observaciones=observations,
                        estado=SoilAnalysisStatusEnum.processing,
                        cantidad_imagenes=len(files_content)
                    )
                )

                # Guardar cambios después de cada lote
                self.soil_analysis_repository.save_changes()
                
                analysis_id = analysis.id
                
                # Agregar el procesamiento de lotes como tarea en segundo plano
                background_tasks.add_task(
                    self._process_batches,
                    files_content,
                    task_id,
                    analysis_id  # Usar el ID del monitoreo creado
                )
                
                return {
                    "analysis_id": analysis_id,
                    "status": "processing",
                    "message": f"Procesando {len(files_content)} imágenes en segundo plano",
                    "total_images": len(files_content)
                }

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error en proceso background: {str(e)}")
            try:
                with SessionLocal() as db:
                    soil_analysis_repository = SoilAnalysisRepository(db)
                    analysis = soil_analysis_repository.get_analysis_by_task_id(task_id)
                    if analysis:
                        analysis.estado = SoilAnalysisStatusEnum.failed
                        soil_analysis_repository.save_changes()
            except Exception as e:
                logger.error(f"Error actualizando estado a failed: {str(e)}")