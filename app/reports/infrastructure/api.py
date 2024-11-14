# app/reports/infrastructure/api.py
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.reports.application.generate_financial_report_use_case import GenerateFinancialReportUseCase
from app.reports.domain.schemas import FarmFinancialReport
from app.user.domain.schemas import UserInDB

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/financial", response_model=FarmFinancialReport)
async def generate_financial_report(
    farm_id: int,
    start_date: date,
    end_date: date,
    plot_id: Optional[int] = None,
    crop_id: Optional[int] = None,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> FarmFinancialReport:
    """
    Genera un reporte financiero detallado.
    
    Parámetros:
    - farm_id: ID de la finca
    - start_date: Fecha de inicio del período (YYYY-MM-DD)
    - end_date: Fecha fin del período (YYYY-MM-DD)
    - plot_id: ID del lote (opcional)
    - crop_id: ID del cultivo (opcional)
    """
    use_case = GenerateFinancialReportUseCase(db)
    return use_case.generate_report(
        farm_id=farm_id,
        start_date=start_date,
        end_date=end_date,
        plot_id=plot_id,
        crop_id=crop_id,
        current_user=current_user
    )