from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.plot.domain.schemas import PlotCreate, PlotResponse
from app.plot.application.create_plot_use_case import CreatePlotUseCase
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from app.plot.domain.schemas import PlotListResponse
from app.plot.application.list_plots_use_case import ListPlotsUseCase

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
        
@router.get("/list/{finca_id}", response_model=PlotListResponse, status_code=status.HTTP_200_OK)
def list_plots(
    finca_id: int,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    list_plots_use_case = ListPlotsUseCase(db)
    try:
        return list_plots_use_case.execute(current_user, finca_id)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar los lotes: {str(e)}"
        )