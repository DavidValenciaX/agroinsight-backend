from sqlalchemy.orm import Session
from app.soil_analysis.domain.schemas import PredictionServiceResponse
from app.soil_analysis.infrastructure.orm_models import SoilAnalysisStatusEnum
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

class SoilAnalysisUseCase:
    """Caso de uso para procesar análisis de suelo"""

    def __init__(self, db: Session):
        self.db = db
        self.cultural_practices_repository = CulturalPracticesRepository(db)
        self.farm_service = FarmService(db)
        self.plot_repository = PlotRepository(db)
        self.cloudinary_service = CloudinaryService()
        self.task_service = TaskService(db)
        self._environment = os.getenv('RAILWAY_ENVIRONMENT_NAME', 'development')
        self.soil_analysis_repository = SoilAnalysisRepository(db)

    async def analyze_soil(self, files: list[UploadFile], task_id: int, observations: str, current_user: UserInDB):
        """
        Ejecuta el caso de uso completo de análisis de suelo
        
        Args:
            files: Lista de archivos de imagen
            task_id: ID de la tarea de análisis de suelo
            observations: Observaciones generales
            current_user: Usuario actual
            
        Returns:
            dict: Resultados del análisis de imágenes
        """
        # Validar número máximo de imágenes
        if len(files) > 15:
            raise DomainException(
                message="Se pueden procesar máximo 15 imágenes por llamada",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        # Validar tipos de archivo permitidos
        for file in files:
            if not file.content_type in ["image/jpeg", "image/png"]:
                raise DomainException(
                    message=f"Archivo {file.filename} no es una imagen válida. Solo se permiten archivos JPG y PNG",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        # Validar que la tarea existe y el usuario tiene acceso
        task = self.cultural_practices_repository.get_task_by_id(task_id)
        if not task:
            raise DomainException(
                message="La tarea especificada no existe",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Validar que la tarea es de tipo análisis de suelo
        task_type = self.cultural_practices_repository.get_task_type_by_id(task.tipo_labor_id)
        if not task_type or task_type.nombre != TaskService.ANALISIS_SUELO:
            raise DomainException(
                message="La tarea debe ser de tipo 'Análisis de suelo'",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        lote = self.plot_repository.get_plot_by_id(task.lote_id)
        if not lote:
            raise DomainException(
                message="El lote especificado no existe",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Obtener predicciones del servicio externo
        analysis_results = await self._get_predictions(files)

        # Procesar resultados y guardar en BD
        result = await self.process_analysis(
            analysis_results,
            files,
            task_id,
            observations
        )

        return SoilAnalysisResponse(
            analysis_id=result["analysis_id"],
            results=analysis_results.results,
            message=analysis_results.message
        )

    async def _get_predictions(self, files: list[UploadFile]) -> PredictionServiceResponse:
        """
        Obtiene las predicciones del servicio externo de análisis de imágenes
        """
        service_url = f"{SOIL_ANALYSIS_SERVICE_URL}/soil-analysis/predict"
        logger.info(f"Making request to: {service_url}")
        
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            verify=False,
            follow_redirects=True,
            transport=httpx.AsyncHTTPTransport(retries=3)
        ) as client:
            try:
                files_to_upload = [
                    ("files", (file.filename, await file.read(), file.content_type))
                    for file in files
                ]
                
                logger.info("Sending files to prediction service...")
                response = await client.post(
                    service_url,
                    files=files_to_upload
                )
                logger.info(f"Response status code: {response.status_code}")
                
            except httpx.ConnectError as e:
                logger.error(f"Connection error: {str(e)}")
                raise DomainException(
                    message=f"No se pudo conectar al servicio de análisis: {str(e)}",
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            except httpx.TimeoutException as e:
                logger.error(f"Timeout error: {str(e)}")
                raise DomainException(
                    message="El servicio de análisis tardó demasiado en responder",
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT
                )

        if response.status_code not in [200, 207]:
            raise DomainException(
                message="Error al procesar las imágenes",
                status_code=response.status_code
            )
            
        # Resetear la posición de lectura de los archivos
        for file in files:
            await file.seek(0)
            
        return PredictionServiceResponse(**response.json())

    async def process_analysis(self, analysis_results: SoilAnalysisResponse, files: list[UploadFile], task_id: int, observations: str):
        """
        Procesa los resultados de la análisis y los guarda en la base de datos
        
        Args:
            detection_results: Resultados del servicio de análisis
            files: Archivos de imagen subidos
            task_id: ID de la tarea de análisis de suelo
            observations: Observaciones generales
            
        Returns:
            SoilAnalysisResponse: Resultados procesados
        """

        # Crear análisis de suelo
        analysis = self.soil_analysis_repository.create_analysis(
            SoilAnalysisCreate(
                tarea_labor_id=task_id,
                fecha_analisis=datetime_utc_time().date(),
                observaciones=observations,
                estado=SoilAnalysisStatusEnum.processing,
                cantidad_imagenes=len(files)
            )
        )

        # Procesar cada detección individual
        for index, result in enumerate(analysis_results.results):
            if result.status == "success":
                # Generar ruta incluyendo el entorno
                image_folder = f"{self._environment}/soil_analysis/task_{task_id}"
                
                # Subir imagen a Cloudinary
                cloudinary_result = await self.cloudinary_service.upload_image(
                    files[index],
                    image_folder
                )
                
                predicted_class = self.soil_analysis_repository.get_soil_type_by_name(result.predicted_class)

                self.soil_analysis_repository.create_classification(
                    SoilClassificationCreate(
                        analisis_suelo_id=analysis.id,
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

        self.soil_analysis_repository.save_changes()
        
        try:
            total_classifications = len(self.soil_analysis_repository.get_classifications_by_analysis_id(analysis.id))
            if total_classifications == 0:
                analysis.estado = SoilAnalysisStatusEnum.failed
            elif total_classifications < analysis.cantidad_imagenes:
                analysis.estado = SoilAnalysisStatusEnum.partial
            else:
                analysis.estado = SoilAnalysisStatusEnum.completed
                
            self.soil_analysis_repository.save_changes()
        except Exception as e:
            logger.error(f"Error actualizando estado del análisis: {str(e)}")
        
        return {
            "analysis_id": analysis.id,
            "results": analysis_results.results,
            "message": analysis_results.message
        }