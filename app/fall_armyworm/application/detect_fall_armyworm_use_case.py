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
    FallArmywormDetectionCreate
)
from typing import List, Dict
import math
import asyncio
from app.infrastructure.db.connection import SessionLocal

load_dotenv(override=True)

logger = logging.getLogger(__name__)
ARMYWORM_SERVICE_URL = os.getenv('ARMYWORM_SERVICE_URL', 'http://localhost:8080')

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
        self.fall_armyworm_repository = FallArmywormRepository(db)

    async def detect_fall_armyworm(self, files: list[UploadFile], task_id: int, observations: str, current_user: UserInDB):
        """
        Ejecuta el caso de uso completo de detección de gusano cogollero
        
        Args:
            files: Lista de archivos de imagen
            task_id: ID de la tarea de monitoreo fitosanitario
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

        # Obtener predicciones del servicio externo
        detection_results = await self._get_predictions(files)
        
        # Procesar resultados y guardar en BD
        result = await self.process_detection(
            detection_results,
            files,
            task_id,
            observations,
            current_user
        )
        
        # Construir la respuesta con el formato correcto
        return FallArmywormDetectionResult(
            monitoring_id=result["monitoring_id"],
            results=detection_results.results,
            message=detection_results.message
        )

    async def _get_predictions(self, files: list[UploadFile]) -> dict:
        """
        Obtiene las predicciones del servicio externo de análisis de imágenes
        """
        service_url = f"{ARMYWORM_SERVICE_URL}/fall-armyworm/predict"
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
            
        return FallArmywormDetectionResult(**response.json())

    async def process_detection(self, detection_results: FallArmywormDetectionResult, files: list[UploadFile], task_id: int, observations: str, current_user: UserInDB):
        """
        Procesa los resultados de la detección y los guarda en la base de datos
        
        Args:
            detection_results: Resultados del servicio de detección
            files: Archivos de imagen subidos
            task_id: ID de la tarea de monitoreo fitosanitario
            observations: Observaciones generales
            current_user: Usuario actual
            
        Returns:
            FallArmywormDetectionResult: Resultados procesados
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
        monitoreo = self.fall_armyworm_repository.create_monitoreo(
            MonitoreoFitosanitarioCreate(
                tarea_labor_id=task_id,
                fecha_monitoreo=datetime_utc_time(),
                observaciones=observations,
                estado=EstadoMonitoreoEnum.processing,
                cantidad_imagenes=len(files)
            )
        )

        # Procesar cada detección individual
        for index, result in enumerate(detection_results.results):
            if result.status == "success":
                # Generar ruta incluyendo el entorno
                image_folder = f"{self._environment}/fall_armyworm/task_{task_id}"
                
                # Subir imagen a Cloudinary
                cloudinary_result = await self.cloudinary_service.upload_image(
                    files[index],
                    image_folder
                )

                self.fall_armyworm_repository.create_detection(
                    FallArmywormDetectionCreate(
                        monitoreo_fitosanitario_id=monitoreo.id,
                        imagen_url=cloudinary_result["url"],
                        imagen_public_id=cloudinary_result["public_id"],
                        resultado_deteccion=result.predicted_class,
                        confianza_deteccion=result.confidence,
                        prob_leaf_with_larva=result.probabilities.leaf_with_larva,
                        prob_healthy_leaf=result.probabilities.healthy_leaf,
                        prob_damaged_leaf=result.probabilities.damaged_leaf
                    )
                )

        self.fall_armyworm_repository.save_changes()
        
        return {
            "monitoring_id": monitoreo.id,
            "results": detection_results.results,
            "message": detection_results.message
        }

    async def process_images_in_background(
        self,
        files_content: List[FileContent],
        task_id: int,
        observations: str,
        user_id: int
    ):
        """
        Procesa imágenes en lotes de 15 en segundo plano
        """
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
                    logger.error(f"Tarea {task_id} no encontrada")
                    return

                lote = self.plot_repository.get_plot_by_id(task.lote_id)
                if not lote or not self.farm_service.user_is_farm_admin(user_id, lote.finca_id):
                    logger.error(f"Usuario {user_id} sin acceso a tarea {task_id}")
                    return

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

                # Procesar imágenes en lotes de 15
                batch_size = 15
                total_batches = math.ceil(len(files_content) / batch_size)

                for batch_num in range(total_batches):
                    start_idx = batch_num * batch_size
                    end_idx = min((batch_num + 1) * batch_size, len(files_content))
                    batch_files = files_content[start_idx:end_idx]

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
                            continue

                        detection_results = FallArmywormDetectionResult(**response.json())

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
                                        monitoreo_fitosanitario_id=monitoreo.id,
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
                        
                        # Pequeña pausa entre lotes
                        await asyncio.sleep(1)

                    except Exception as e:
                        logger.error(f"Error procesando lote {batch_num + 1}/{total_batches}: {str(e)}")
                        continue
                    
                # Actualizar estado del monitoreo
                try:
                    total_detections = len(self.fall_armyworm_repository.get_detections_by_monitoreo_id(monitoreo.id))
                    if total_detections == 0:
                        monitoreo.estado = EstadoMonitoreoEnum.failed
                    elif total_detections < monitoreo.cantidad_imagenes:
                        monitoreo.estado = EstadoMonitoreoEnum.partial
                    else:
                        monitoreo.estado = EstadoMonitoreoEnum.completed
                    
                    self.fall_armyworm_repository.save_changes()
                except Exception as e:
                    logger.error(f"Error actualizando estado del monitoreo: {str(e)}")

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

    async def create_initial_monitoring(self, task_id: int, observations: str, total_images: int) -> int:
        """
        Crea un registro inicial de monitoreo y retorna su ID
        """
        with SessionLocal() as db:
            self.db = db
            self.fall_armyworm_repository = FallArmywormRepository(db)
            
            monitoreo = self.fall_armyworm_repository.create_monitoreo(
                MonitoreoFitosanitarioCreate(
                    tarea_labor_id=task_id,
                    fecha_monitoreo=datetime_utc_time(),
                    observaciones=observations,
                    estado=EstadoMonitoreoEnum.processing,
                    cantidad_imagenes=total_images
                )
            )
            self.fall_armyworm_repository.save_changes()
            return monitoreo.id