from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List
import httpx
import logging
from sqlalchemy.orm import Session
from app.soil_analysis.application.get_analysis_status_use_case import GetAnalysisStatusUseCase
from app.soil_analysis.application.get_analysis_use_case import GetAnalysisUseCase
from app.soil_analysis.application.soil_analysis_background_use_case import SoilAnalysisBackgroundUseCase
from app.soil_analysis.domain.schemas import FileContent, SoilAnalysisResult
from app.infrastructure.db.connection import getDb, SessionLocal
from app.infrastructure.security.jwt_middleware import get_current_user
from app.user.domain.schemas import UserInDB
from app.soil_analysis.application.soil_analysis_use_case import SoilAnalysisUseCase
from app.infrastructure.common.common_exceptions import DomainException
import os
from dotenv import load_dotenv
from app.logs.application.decorators.log_decorator import log_activity
from app.logs.application.services.log_service import LogActionType

load_dotenv(override=True)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener URL del servicio de análisis de imágenes desde variable de entorno
SOIL_ANALYSIS_SERVICE_URL = os.getenv('SOIL_ANALYSIS_SERVICE_URL', 'http://localhost:5000')

router = APIRouter(prefix="/soil-analysis", tags=["soil analysis"])

@router.post("/predict")
@log_activity(
    action_type=LogActionType.REGISTER_SOIL_ANALYSIS,
    table_name="analisis_suelo",
    description="Registro de nuevo análisis de suelo",
    get_record_id=lambda *args, **kwargs: kwargs.get('result', {}).get('analysis_id'),
    get_new_value=lambda *args, **kwargs: {
        "task_id": kwargs.get('task_id'),
        "observations": kwargs.get('observations'),
        "total_images": len(kwargs.get('files', []))
    }
)
async def predict_images(
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    task_id: int = Form(...),
    observations: str = Form(None),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Endpoint para realizar análisis de suelo.
    
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
            await file.seek(0)  # Reset the pointer to the beginning

        # Obtener user_id en lugar de current_user completo
        user_id = current_user.id

        if len(files) <= 15:
            # Procesar normalmente
            soil_analysis_use_case = SoilAnalysisUseCase(SessionLocal())
            result = await soil_analysis_use_case.analyze_soil(
                files=files,
                task_id=task_id,
                observations=observations,
                current_user=current_user
            )
            return result
        else:
            # Procesar en segundo plano
            soil_analysis_background_use_case = SoilAnalysisBackgroundUseCase(None)
            return await soil_analysis_background_use_case.process_images_in_background(
                files_content=files_content,
                task_id=task_id,
                observations=observations,
                user_id=user_id,
                background_tasks=background_tasks
            )
            
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando las imágenes: {str(e)}"
        ) from e

@router.get("/test-soil-analysis-connection", status_code=status.HTTP_200_OK)
@log_activity(
    action_type=LogActionType.VERIFY_CONNECTION,
    table_name="analisis_suelo",
    description="Verificación de conexión con servicio de análisis de suelo",
    get_new_value=lambda *args, **kwargs: {
        "service_url": SOIL_ANALYSIS_SERVICE_URL,
        "status": "success" if kwargs.get('result') else "error"
    }
)
async def test_connection(request: Request):
    """Endpoint para probar la conexión con el servicio de análisis"""
    try:
        async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
            response = await client.get(f"{SOIL_ANALYSIS_SERVICE_URL}/soil-analysis/health")
            result = {
                "status": "success",
                "service_url": SOIL_ANALYSIS_SERVICE_URL,
                "response": response.json()
            }
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=result
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error conectando con el servicio de análisis: {str(e)}"
        ) from e
        
@router.get("/analysis/{analysis_id}/status")
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="analisis_suelo",
    description="Consulta de estado de análisis de suelo"
)
async def get_processing_status(
    request: Request,
    analysis_id: int,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Consulta el estado del procesamiento de imágenes para una tarea
    """
    try:
        get_analysis_status_use_case = GetAnalysisStatusUseCase(db)
        return get_analysis_status_use_case.get_analysis_status(analysis_id)
        
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error consultando estado: {str(e)}"
        ) from e
        
@router.get("/analysis/{analysis_id}", response_model=SoilAnalysisResult)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="analisis_suelo",
    description="Consulta de resultados de análisis de suelo"
)
async def get_analysis_results(
    request: Request,
    analysis_id: int,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obtiene los resultados de un análisis de suelo específico
    
    Args:
        analysis_id: ID del análisis de suelo
        db: Sesión de base de datos
        current_user: Usuario autenticado
    """
    try:
        get_analysis_use_case = GetAnalysisUseCase(db)
        return get_analysis_use_case.get_analysis(analysis_id, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo resultados del análisis: {str(e)}"
        ) from e