from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.farm.domain.schemas import FarmCreate, FarmResponse, FarmListResponse, PaginatedFarmListResponse
from app.farm.application.create_farm_use_case import CreateFarmUseCase
from app.farm.application.list_farms_use_case import ListFarmsUseCase
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import Query

router = APIRouter(prefix="/farm", tags=["farm"])

@router.post("/create", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
def create_farm(
    farm: FarmCreate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    crear_farm_use_case = CreateFarmUseCase(db)
    try:
        return crear_farm_use_case.execute(farm, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al crear la finca: {str(e)}"
        )
        
@router.get("/list", response_model=PaginatedFarmListResponse, status_code=status.HTTP_200_OK)
def list_farms(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    list_farms_use_case = ListFarmsUseCase(db)
    try:
        return list_farms_use_case.execute(current_user, page, per_page)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar las fincas: {str(e)}"
        )