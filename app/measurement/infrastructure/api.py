from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List
from app.infrastructure.common.common_exceptions import DomainException
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.measurement.domain.schemas import UnitsListResponse
from app.measurement.application.list_units_use_case import ListUnitsUseCase
from app.user.domain.schemas import UserInDB
from app.logs.application.decorators.log_decorator import log_activity
from app.logs.application.services.log_service import LogActionType

measurement_router = APIRouter(prefix="/measurement", tags=["measurement"])

@measurement_router.get("/units", response_model=UnitsListResponse)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="unidad_medida",
    description="Consulta de unidades de medida"
)
async def list_units(
    request: Request,
    db: Session = Depends(getDb), 
    current_user: UserInDB = Depends(get_current_user)
) -> UnitsListResponse:
    """
    Obtiene la lista de todas las unidades de medida.

    Args:
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario autenticado actual.

    Returns:
        UnitsListResponse: Objeto de respuesta con la lista de unidades de medida.
    """
    list_units_use_case = ListUnitsUseCase(db)
    try:
        return list_units_use_case.list_units()
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener las unidades de medida: {str(e)}"
        ) from e
