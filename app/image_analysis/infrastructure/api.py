from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Form
from typing import List
import httpx
import logging
from sqlalchemy.orm import Session
from app.infrastructure.db.connection import getDb
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
    files: List[UploadFile] = File(...),
    task_id: int = Form(...),
    observations: str = Form(None),
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Endpoint para analizar imágenes y detectar el gusano cogollero.
    
    Args:
        files: Lista de archivos de imagen
        task_id: ID de la tarea de monitoreo fitosanitario
        observations: Observaciones generales (opcional)
        db: Sesión de base de datos
        current_user: Usuario autenticado
    """

    try:
        detect_fall_armyworm_use_case = DetectFallArmywormUseCase(db)
        result = await detect_fall_armyworm_use_case.detect_fall_armyworm(
            files=files,
            task_id=task_id,
            observations=observations,
            current_user=current_user
        )
        return result
        
    except DomainException as e:
        raise e
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