from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Form, BackgroundTasks
from typing import List
import httpx
import logging
from sqlalchemy.orm import Session
from app.image_analysis.domain.schemas import FileContent
from app.infrastructure.db.connection import getDb, SessionLocal
from app.infrastructure.security.jwt_middleware import get_current_user
from app.user.domain.schemas import UserInDB
from app.image_analysis.application.detect_fall_armyworm_use_case import DetectFallArmywormUseCase
from app.infrastructure.common.common_exceptions import DomainException
import os
from dotenv import load_dotenv
import socket
import platform

load_dotenv(override=True)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener URL del servicio de análisis de imágenes desde variable de entorno
ARMYWORM_SERVICE_URL = os.getenv('ARMYWORM_SERVICE_URL', 'http://localhost:8080')
logger.info(f"ARMYWORM_SERVICE_URL configured as: {ARMYWORM_SERVICE_URL}")

router = APIRouter(tags=["image analysis"])

@router.post("/predict")
async def predict_images(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    task_id: int = Form(...),
    observations: str = Form(None),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Endpoint para analizar imágenes y detectar el gusano cogollero.
    
    Args:
        files: Lista de archivos de imagen
        task_id: ID de la tarea de monitoreo fitosanitario
        observations: Observaciones generales (opcional)
        current_user: Usuario autenticado
    """

    try:
        # Leer el contenido de los archivos antes de que termine la solicitud
        files_content = []
        for file in files:
            content = await file.read()
            files_content.append(FileContent(
                filename=file.filename,
                content=content,
                content_type=file.content_type
            ))

        # Obtener user_id en lugar de current_user completo
        user_id = current_user.id

        if len(files) <= 15:
            # Procesar normalmente
            detect_fall_armyworm_use_case = DetectFallArmywormUseCase(SessionLocal())
            result = await detect_fall_armyworm_use_case.detect_fall_armyworm(
                files=files,
                task_id=task_id,
                observations=observations,
                user_id=user_id
            )
            return result
        else:
            # Procesar en segundo plano
            detect_fall_armyworm_use_case = DetectFallArmywormUseCase(None)  # Pasamos None, inicializaremos dentro del background task
            background_tasks.add_task(
                detect_fall_armyworm_use_case.process_images_in_background,
                files_content=files_content,
                task_id=task_id,
                observations=observations,
                user_id=user_id
            )
            return {
                "status": "processing",
                "message": f"Procesando {len(files_content)} imágenes en segundo plano",
                "total_images": len(files_content)
            }
            
    except DomainException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando las imágenes: {str(e)}"
        )

@router.get("/test-armyworm-connection")
async def test_connection():
    """Endpoint para probar la conexión con el servicio de análisis"""
    try:
        async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
            response = await client.get(f"{ARMYWORM_SERVICE_URL}/health")
            return {
                "status": "success",
                "service_url": ARMYWORM_SERVICE_URL,
                "response": response.json()
            }
    except Exception as e:
        return {
            "status": "error",
            "service_url": ARMYWORM_SERVICE_URL,
            "error": str(e)
        }
        
@router.get("/predict/{task_id}/status")
async def get_processing_status(
    task_id: int,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Consulta el estado del procesamiento de imágenes para una tarea
    """
    try:
        detect_fall_armyworm_use_case = DetectFallArmywormUseCase(db)
        monitoreo = detect_fall_armyworm_use_case.fall_armyworm_repository.get_monitoreo_by_task_id(task_id)
        
        if not monitoreo:
            return {
                "status": "not_found",
                "message": "No se encontró un monitoreo para esta tarea"
            }
            
        detections = detect_fall_armyworm_use_case.fall_armyworm_repository.get_detections_by_monitoreo_id(monitoreo.id)
        
        return {
            "status": "completed",
            "total_processed": len(detections),
            "monitoreo_id": monitoreo.id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error consultando estado: {str(e)}"
        )