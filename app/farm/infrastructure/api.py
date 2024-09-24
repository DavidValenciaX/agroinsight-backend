from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.db.connection import getDb
from app.core.security.jwt_middleware import get_current_user
from app.farm.domain.schemas import FincaCreate, FincaResponse
from app.farm.application.crear_finca_use_case import CrearFincaUseCase
from app.user.domain.schemas import UserInDB
from app.farm.domain.exceptions import DomainException

router = APIRouter(prefix="/farm", tags=["farm"])

@router.post("/create", response_model=FincaResponse, status_code=status.HTTP_201_CREATED)
def create_finca(
    finca: FincaCreate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    crear_finca_use_case = CrearFincaUseCase(db)
    try:
        return crear_finca_use_case.execute(finca, current_user)
    except DomainException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al crear la finca: {str(e)}"
        )