"""
Este módulo define las rutas de la API para la gestión de lotes.

Incluye endpoints para la creación de lotes y el listado de lotes de una finca específica.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.plot.domain.schemas import PlotCreate
from app.plot.application.create_plot_use_case import CreatePlotUseCase
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from app.plot.domain.schemas import PaginatedPlotListResponse
from app.plot.application.list_plots_use_case import ListPlotsUseCase
from fastapi import Query
from app.logs.application.decorators.log_decorator import log_activity
from app.logs.application.services.log_service import LogActionType

router = APIRouter(tags=["plot"])

def get_created_plot_id(*args, **kwargs) -> int:
    """Obtiene el ID del lote creado desde el resultado de la operación."""
    result = kwargs.get('result')
    if isinstance(result, dict) and 'id' in result:
        return result['id']
    return None

def get_plot_data(*args, **kwargs) -> dict:
    """Obtiene los datos del lote desde los argumentos."""
    plot_data = next((arg for arg in args if isinstance(arg, PlotCreate)), None)
    if plot_data:
        return plot_data.model_dump()
    return None

@router.post("/plot/create", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
@log_activity(
    action_type=LogActionType.REGISTER_PLOT,
    table_name="lote",
    description=(
        "Creación de nuevo lote en el sistema. "
        "Se registran los detalles del lote incluyendo nombre, área, "
        "coordenadas y su asociación con la finca correspondiente"
    ),
    get_record_id=get_created_plot_id,
    get_new_value=get_plot_data
)
async def create_plot(
    request: Request,
    plot: PlotCreate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
)-> SuccessResponse:
    """
    Crea un nuevo lote en el sistema dentro de una finca específica.

    Parameters:
        plot (PlotCreate): Datos del lote a crear.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que el lote fue creado exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante la creación del lote o si hay inconsistencia en los IDs de finca.
    """
    create_plot_use_case = CreatePlotUseCase(db)
    try:
        return create_plot_use_case.create_plot(plot, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al crear el lote: {str(e)}"
        )
        
@router.get("/farm/{farm_id}/plot/list", response_model=PaginatedPlotListResponse, status_code=status.HTTP_200_OK)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="lote",
    description=(
        "Consulta del listado paginado de lotes asociados a una finca específica. "
        "Mostrando 10 elementos por página"
    )
)
async def list_plots_by_farm(
    request: Request,
    farm_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
)-> PaginatedPlotListResponse:
    """
    Lista todos los lotes de una finca específica.

    Parameters:
        farm_id (int): ID de la finca.
        page (int): Número de página.
        per_page (int): Elementos por página.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        PaginatedPlotListResponse: Una lista paginada de lotes.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de la lista de lotes.
    """
    list_plots_use_case = ListPlotsUseCase(db)
    try:
        return list_plots_use_case.list_plots(current_user, farm_id, page, per_page)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar los lotes: {str(e)}"
        )
