# app/reports/infrastructure/api.py
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List
from enum import Enum
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.reports.application.generate_financial_report_use_case import GenerateFinancialReportUseCase
from app.reports.domain.schemas import FarmFinancialReport
from app.user.domain.schemas import UserInDB
from app.logs.application.decorators.log_decorator import log_activity
from app.logs.application.services.log_service import LogActionType

router = APIRouter(prefix="/reports", tags=["reports"])

class ReportGroupBy(str, Enum):
    """Opciones para agrupar el reporte"""
    NONE = "none"  # Sin agrupación especial
    TASK_TYPE = "task_type"  # Agrupar por tipo de tarea
    MONTH = "month"  # Agrupar por mes
    COST_TYPE = "cost_type"  # Agrupar por tipo de costo (mano obra, insumos, maquinaria)

@router.get("/financial", response_model=FarmFinancialReport)
@log_activity(
    action_type=LogActionType.GENERATE_REPORT,
    table_name="finca",
    description="Generación de reporte financiero"
)
async def generate_financial_report(
    request: Request,
    farm_id: int,
    start_date: date,
    end_date: date,
    plot_id: Optional[int] = None,
    crop_id: Optional[int] = None,
    min_cost: Optional[float] = None,
    max_cost: Optional[float] = None,
    task_types: Optional[List[str]] = Query(None),
    group_by: ReportGroupBy = ReportGroupBy.NONE,
    only_profitable: Optional[bool] = None,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> FarmFinancialReport:
    """
    Genera un reporte financiero detallado con opciones de filtrado.
    
    Parámetros:
    - farm_id: ID de la finca
    - start_date: Fecha de inicio del período (YYYY-MM-DD)
    - end_date: Fecha fin del período (YYYY-MM-DD)
    - plot_id: ID del lote (opcional)
    - crop_id: ID del cultivo (opcional)
    - min_cost: Costo mínimo para filtrar tareas/cultivos
    - max_cost: Costo máximo para filtrar tareas/cultivos
    - task_types: Lista de tipos de tareas a incluir
    - group_by: Tipo de agrupación para el reporte
    - only_profitable: Si es True, solo incluye elementos con ganancia positiva
    """
    use_case = GenerateFinancialReportUseCase(db)
    return use_case.generate_report(
        farm_id=farm_id,
        start_date=start_date,
        end_date=end_date,
        plot_id=plot_id,
        crop_id=crop_id,
        min_cost=min_cost,
        max_cost=max_cost,
        task_types=task_types,
        group_by=group_by,
        only_profitable=only_profitable,
        current_user=current_user
    )