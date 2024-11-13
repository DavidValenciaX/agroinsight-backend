from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Form, BackgroundTasks
from typing import List
from fastapi.responses import JSONResponse
import httpx
import logging
from sqlalchemy.orm import Session
from app.cultural_practices.application.services.task_service import TaskService
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.fall_armyworm.application.get_monitoring_status_use_case import GetMonitoringStatusUseCase
from app.fall_armyworm.application.get_monitoring_use_case import GetMonitoringUseCase
from app.fall_armyworm.domain.schemas import FileContent, MonitoreoFitosanitarioResult
from app.fall_armyworm.infrastructure.sql_repository import FallArmywormRepository
from app.infrastructure.db.connection import getDb, SessionLocal
from app.infrastructure.security.jwt_middleware import get_current_user
from app.user.domain.schemas import UserInDB
from app.fall_armyworm.application.detect_fall_armyworm_use_case import DetectFallArmywormUseCase
from app.infrastructure.common.common_exceptions import DomainException
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener URL del servicio de análisis de imágenes desde variable de entorno
ARMYWORM_SERVICE_URL = os.getenv('ARMYWORM_SERVICE_URL', 'http://localhost:8080')

router = APIRouter(prefix="/fall-armyworm", tags=["fall armyworm analysis"])

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
            await file.seek(0)

        # Obtener user_id en lugar de current_user completo
        user_id = current_user.id

        if len(files) <= 15:
            # Procesar normalmente
            detect_fall_armyworm_use_case = DetectFallArmywormUseCase(SessionLocal())
            result = await detect_fall_armyworm_use_case.detect_fall_armyworm(
                files=files,
                task_id=task_id,
                observations=observations,
                current_user=current_user
            )
            # Modificar la respuesta para incluir el monitoring_id
            return {
                "monitoring_id": result.monitoring_id,
                "results": result.results,
                "message": result.message
            }
        else:
            # Procesar en segundo plano
            detect_fall_armyworm_use_case = DetectFallArmywormUseCase(None)
            # Crear el monitoreo antes de iniciar el procesamiento en segundo plano
            monitoring_id = await detect_fall_armyworm_use_case.create_initial_monitoring(
                task_id=task_id,
                observations=observations,
                total_images=len(files_content)
            )
            
            background_tasks.add_task(
                detect_fall_armyworm_use_case.process_images_in_background,
                files_content=files_content,
                task_id=task_id,
                observations=observations,
                user_id=user_id,
                monitoring_id=monitoring_id
            )
            
            return {
                "monitoring_id": monitoring_id,
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
        ) from e

@router.get("/test-armyworm-connection", status_code=status.HTTP_200_OK)
async def test_connection():
    """Endpoint para probar la conexión con el servicio de análisis"""
    try:
        async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
            response = await client.get(f"{ARMYWORM_SERVICE_URL}/fall-armyworm/health")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "service_url": ARMYWORM_SERVICE_URL,
                    "response": response.json()
                }
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error conectando con el servicio de análisis: {str(e)}"
        ) from e

@router.get("/monitoring/{monitoring_id}/status")
async def get_monitoring_status(
    monitoring_id: int,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Consulta el estado del procesamiento de imágenes para una tarea
    """
    try:
        get_monitoring_status_use_case = GetMonitoringStatusUseCase(db)
        return get_monitoring_status_use_case.get_monitoring_status(monitoring_id)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error consultando estado: {str(e)}"
        ) from e

@router.get("/monitoring/{monitoring_id}", response_model=MonitoreoFitosanitarioResult)
async def get_monitoring_results(
    monitoring_id: int,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obtiene los resultados de un monitoreo fitosanitario específico
    
    Args:
        monitoreo_id: ID del monitoreo fitosanitario
        db: Sesión de base de datos
        current_user: Usuario autenticado
    """
    try:
        get_monitoring_use_case = GetMonitoringUseCase(db)
        return get_monitoring_use_case.get_monitoring(monitoring_id, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo resultados del monitoreo: {str(e)}"
        ) from e