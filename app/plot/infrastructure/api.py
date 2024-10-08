"""
Este módulo define las rutas de la API para la gestión de lotes.

Incluye endpoints para la creación de lotes y el listado de lotes de una finca específica.
"""

from fastapi import APIRouter, Depends, HTTPException, status
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

router = APIRouter(prefix="/plot", tags=["plot"])

@router.post("/create", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def create_plot(
    plot: PlotCreate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Crea un nuevo lote en el sistema.

    Parameters:
        plot (PlotCreate): Datos del lote a crear.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que el lote fue creado exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante la creación del lote.
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
        
@router.get("/list/{finca_id}", response_model=PaginatedPlotListResponse, status_code=status.HTTP_200_OK)
def list_plots(
    finca_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Lista todos los lotes de una finca específica.

    Parameters:
        finca_id (int): ID de la finca.
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
        return list_plots_use_case.list_plots(current_user, finca_id, page, per_page)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar los lotes: {str(e)}"
        )