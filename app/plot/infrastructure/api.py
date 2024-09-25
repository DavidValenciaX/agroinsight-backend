from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.plot.domain.schemas import PlotCreate, PlotResponse
from app.plot.application.create_plot_use_case import CreatePlotUseCase
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from app.plot.domain.schemas import PaginatedPlotListResponse
from app.plot.application.list_plots_use_case import ListPlotsUseCase
from fastapi import Query

router = APIRouter(prefix="/plot", tags=["plot"])

@router.post("/create", response_model=PlotResponse, status_code=status.HTTP_201_CREATED)
def create_plot(
    plot: PlotCreate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    create_plot_use_case = CreatePlotUseCase(db)
    try:
        return create_plot_use_case.execute(plot, current_user)
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
    list_plots_use_case = ListPlotsUseCase(db)
    try:
        return list_plots_use_case.execute(current_user, finca_id, page, per_page)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar los lotes: {str(e)}"
        )