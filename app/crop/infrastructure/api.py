"""
Este módulo define las rutas de la API para la gestión de cultivos.

Incluye endpoints para la creación de cultivos y otras operaciones relacionadas.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.crop.domain.schemas import CropCreate
from app.crop.application.create_crop_use_case import CreateCropUseCase
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException

router = APIRouter(tags=["crop"])

@router.post("/crops", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def create_crop(
    crop: CropCreate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Crea un nuevo cultivo en el sistema.

    Parameters:
        crop (CropCreate): Datos del cultivo a crear.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que el cultivo fue creado exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante la creación del cultivo.
    """
    create_crop_use_case = CreateCropUseCase(db)
    try:
        return create_crop_use_case.create_crop(crop, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al crear el cultivo: {str(e)}"
        )

