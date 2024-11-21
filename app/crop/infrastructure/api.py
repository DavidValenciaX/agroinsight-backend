"""
Este módulo define las rutas de la API para la gestión de cultivos.

Incluye endpoints para la creación de cultivos y otras operaciones relacionadas.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.crop.domain.schemas import CropCreate, PaginatedCropListResponse, CropHarvestUpdate
from app.crop.application.create_crop_use_case import CreateCropUseCase
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from app.crop.domain.schemas import CornVarietyListResponse
from app.crop.application.list_corn_varieties_use_case import ListCornVarietiesUseCase
from app.crop.application.list_crops_by_plot_use_case import ListCropsByPlotUseCase
from app.crop.application.update_crop_harvest_use_case import UpdateCropHarvestUseCase
from app.logs.application.services.log_service import LogActionType
from app.logs.application.decorators.log_decorator import log_activity

router = APIRouter(tags=["crop"])

@router.post("/crops", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
@log_activity(
    action_type=LogActionType.CREATE, 
    table_name="cultivo",
    description="Creación de nuevo cultivo en el sistema con datos de variedad, fecha de siembra y lote asociado",
    get_new_value=lambda *args, **kwargs: kwargs.get('crop').dict() if 'crop' in kwargs else None
)
async def create_crop(
    crop: CropCreate,
    request: Request,
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
@log_activity(
    action_type=LogActionType.VIEW, 
    table_name="variedad_maiz",
    description="Consulta del catálogo de variedades de maíz disponibles en el sistema"
)
async def list_corn_varieties(
    request: Request,
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
@log_activity(
    action_type=LogActionType.VIEW, 
    table_name="cultivo",
    description="Consulta paginada de cultivos asociados a un lote específico",
    get_record_id=lambda *args, **kwargs: kwargs.get('plot_id')
)
async def list_crops_by_plot(
    plot_id: int,
    request: Request,
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

@router.put("/crops/{crop_id}/harvest", response_model=SuccessResponse)
@log_activity(
    action_type=LogActionType.REGISTER_HARVEST, 
    table_name="cultivo",
    description="Registro de datos de cosecha y venta para un cultivo específico, incluyendo rendimiento y precio de venta",
    get_record_id=lambda *args, **kwargs: kwargs.get('crop_id'),
    get_old_value=lambda *args, **kwargs: {
        'crop_id': kwargs.get('crop_id')
    },
    get_new_value=lambda *args, **kwargs: kwargs.get('harvest_data').dict() if 'harvest_data' in kwargs else None
)
async def update_crop_harvest(
    crop_id: int,
    harvest_data: CropHarvestUpdate,
    request: Request,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> SuccessResponse:
    """
    Actualiza la información de cosecha y venta de un cultivo.

    Parameters:
        crop_id (int): ID del cultivo a actualizar.
        harvest_data (CropHarvestUpdate): Datos de la cosecha y venta.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        SuccessResponse: Mensaje indicando que la actualización fue exitosa.

    Raises:
        HTTPException: Si ocurre un error durante la actualización.
    """
    try:
        use_case = UpdateCropHarvestUseCase(db)
        return use_case.update_harvest(crop_id, harvest_data, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al actualizar la información de cosecha: {str(e)}"
        ) from e



