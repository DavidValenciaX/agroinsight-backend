from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Form
from typing import List
import httpx
from sqlalchemy.orm import Session
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.user.domain.schemas import UserInDB
from app.image_analysis.application.detect_fall_armyworm_use_case import DetectFallArmywormUseCase
from app.infrastructure.common.common_exceptions import DomainException
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Obtener URL del servicio de análisis de imágenes desde variable de entorno
ARMYWORM_SERVICE_URL = os.getenv('ARMYWORM_SERVICE_URL')

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
    # Validar número máximo de imágenes
    if len(files) > 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se pueden procesar máximo 15 imágenes por llamada"
        )
        
    # Validar tipos de archivo permitidos
    for file in files:
        if not file.content_type in ["image/jpeg", "image/png"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Archivo {file.filename} no es una imagen válida. Solo se permiten archivos JPG y PNG"
            )

    try:
        # Llamar al servicio de análisis
        async with httpx.AsyncClient() as client:
            files_to_upload = [
                ("files", (file.filename, await file.read(), file.content_type))
                for file in files
            ]
            
            response = await client.post(
                f"{ARMYWORM_SERVICE_URL}/predict",
                files=files_to_upload
            )

        if response.status_code not in [200, 207]:
            raise HTTPException(
                status_code=response.status_code,
                detail="Error al procesar las imágenes"
            )
            
        # Resetear la posición de lectura de los archivos
        for file in files:
            await file.seek(0)

        # Procesar resultados y guardar en BD
        use_case = DetectFallArmywormUseCase(db)
        result = await use_case.process_detection(
            response.json(),
            files,
            task_id,
            observations,
            current_user
        )
        
        return result

    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando las imágenes: {str(e)}"
        ) 