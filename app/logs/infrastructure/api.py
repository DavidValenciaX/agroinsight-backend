"""
Este módulo define las rutas de la API para la gestión de logs del sistema.

Incluye endpoints para obtener y consultar los logs de actividad del sistema.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.logs.domain.schemas import ActivityLogResponse
from app.logs.application.get_paginated_logs_use_case import GetPaginatedLogsUseCase
from app.infrastructure.common.common_exceptions import DomainException
from app.user.domain.schemas import UserInDB
from app.logs.application.decorators.log_decorator import log_activity
from app.logs.application.services.log_service import LogActionType

logs_router = APIRouter(prefix="/logs", tags=["logs"])

@logs_router.get("", response_model=List[ActivityLogResponse])
@log_activity(
    action_type=LogActionType.VIEW, 
    table_name="log_actividad",
    description="Consulta de logs del sistema"
)
async def get_system_logs(
    request: Request,
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(100, ge=1, le=100, description="Registros por página"),
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(getDb)
) -> List[ActivityLogResponse]:
    """
    Obtiene los logs del sistema de manera paginada.

    Args:
        request (Request): Objeto de solicitud HTTP.
        page (int): Número de página a recuperar (comienza en 1).
        limit (int): Cantidad de registros por página (máximo 100).
        current_user (UserInDB): Usuario autenticado actual.
        db (Session): Sesión de base de datos.

    Returns:
        List[ActivityLogResponse]: Lista paginada de logs del sistema.

    Raises:
        HTTPException: Si ocurre un error al obtener los logs.
    """
    try:
        get_logs_use_case = GetPaginatedLogsUseCase(db)
        return get_logs_use_case.get_logs(page=page, limit=limit)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener los logs del sistema: {str(e)}"
        ) 