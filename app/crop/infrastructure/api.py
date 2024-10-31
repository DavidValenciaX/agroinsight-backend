"""
Este módulo define las rutas de la API para la gestión de cultivos.

Incluye endpoints para la creación de cultivos y otras operaciones relacionadas.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.crop.domain.schemas import CropCreate, PaginatedCropListResponse
from app.crop.application.create_crop_use_case import CreateCropUseCase
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from app.crop.domain.schemas import CornVarietyListResponse
from app.crop.application.list_corn_varieties_use_case import ListCornVarietiesUseCase
from app.crop.application.list_crops_by_plot_use_case import ListCropsByPlotUseCase

router = APIRouter(tags=["crop"])

@router.post("/crops", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def create_crop(
    crop: CropCreate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> SuccessResponse:
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
        
# endpoint para listar las variedades de maiz

@router.get("/corn-varieties", response_model=CornVarietyListResponse)
def list_corn_varieties(
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> CornVarietyListResponse:
    """
    Lista todas las variedades de maíz disponibles.

    Parameters:
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        CornVarietyListResponse: Lista de variedades de maíz.

    Raises:
        HTTPException: Si ocurre un error al obtener las variedades.
    """
    try:
        use_case = ListCornVarietiesUseCase(db)
        return use_case.list_corn_varieties()
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las variedades de maíz: {str(e)}"
        )

@router.get("/plots/{plot_id}/crops", response_model=PaginatedCropListResponse)
def list_crops_by_plot(
    plot_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> PaginatedCropListResponse:
    """
    Lista todos los cultivos asociados a un lote específico.

    Parameters:
        plot_id (int): ID del lote.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        PaginatedCropListResponse: Lista de cultivos y total.

    Raises:
        HTTPException: Si ocurre un error al obtener los cultivos.
    """
    try:
        use_case = ListCropsByPlotUseCase(db)
        return use_case.list_crops(plot_id, page, per_page, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener los cultivos del lote: {str(e)}"
        )



