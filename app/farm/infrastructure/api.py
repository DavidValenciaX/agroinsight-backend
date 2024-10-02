from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.farm.application.list_farm_users_use_case import ListFarmUsersUseCase
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.farm.domain.schemas import FarmCreate, PaginatedFarmListResponse, FarmUserAssignment, PaginatedFarmUserListResponse
from app.farm.application.create_farm_use_case import CreateFarmUseCase
from app.farm.application.list_farms_use_case import ListFarmsUseCase
from app.farm.application.assign_users_to_farm_use_case import AssignUsersToFarmUseCase
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from app.user.infrastructure.orm_models import User

router = APIRouter(prefix="/farm", tags=["farm"])

@router.post("/create", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
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
        
@router.post("/assign-users", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def assign_users_to_farm(
    assignment_data: FarmUserAssignment,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    assingn_users_use_case = AssignUsersToFarmUseCase(db)
    try:
        return assingn_users_use_case.execute(assignment_data, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al asignar usuario a una finca {str(e)}"
        )
        
@router.get("/{farm_id}/users", response_model=PaginatedFarmUserListResponse, status_code=status.HTTP_200_OK)
def list_farm_users(
    farm_id: int,
    role: str = Query(None, description="Nombre del rol a filtrar"),
    role_id: int = Query(None, description="ID del rol a filtrar"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(getDb)
):
    if role is None and role_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proporcionar 'role' o 'role_id'"
        )
    if role is not None and role_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proporcione 'role' o 'role_id', no ambos"
        )
    
    use_case = ListFarmUsersUseCase(db)
    try:
        return use_case.execute(farm_id, role, role_id, current_user, page, per_page)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error al listar los usuarios de una finca: {str(e)}"
        )