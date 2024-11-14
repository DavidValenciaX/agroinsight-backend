# app/reports/application/generate_financial_report_use_case.py
from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from app.crop.application.services.crop_service import CropService
from app.cultural_practices.application.services.task_service import TaskService
from app.farm.infrastructure.sql_repository import FarmRepository
from app.infrastructure.security.jwt_middleware import get_current_user
from app.reports.infrastructure.sql_repository import FinancialReportRepository
from app.farm.application.services.farm_service import FarmService
from app.reports.domain.schemas import FarmFinancialReport, PlotFinancials, CropFinancials, TaskCost
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import Depends, status

from app.user.domain.schemas import UserInDB

class GenerateFinancialReportUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.repository = FinancialReportRepository(db)
        self.farm_service = FarmService(db)
        self.farm_repository = FarmRepository(db)

    def generate_report(
        self,
        farm_id: int,
        start_date: date,
        end_date: date,
        plot_id: Optional[int] = None,
        crop_id: Optional[int] = None,
        current_user: UserInDB = Depends(get_current_user)
    ) -> FarmFinancialReport:
        """
        Genera un reporte financiero completo.
        
        Args:
            farm_id: ID de la finca
            start_date: Fecha de inicio del período
            end_date: Fecha fin del período
            plot_id: ID del lote (opcional, para filtrar por lote)
            crop_id: ID del cultivo (opcional, para filtrar por cultivo)
            current_user: Usuario actual
        """
        # Validar permisos
        if not self.farm_service.user_is_farm_admin(current_user.id, farm_id):
            raise DomainException(
                message="No tienes permisos para generar reportes de esta finca",
                status_code=status.HTTP_403_FORBIDDEN
            )

        farm = self.farm_repository.get_farm_by_id(farm_id)
        if not farm:
            raise DomainException(
                message="Finca no encontrada",
                status_code=status.HTTP_404_NOT_FOUND
            )

        plots = self.repository.get_farm_plots(farm_id)
        if plot_id:
            plots = [p for p in plots if p.id == plot_id]

        plot_financials = []
        total_farm_cost = Decimal(0)
        total_farm_income = Decimal(0)

        for plot in plots:
            # Obtener todas las tareas del lote para el período
            tasks = self.repository.get_plot_tasks_in_period(plot.id, start_date, end_date)
            task_costs = []
            total_plot_task_cost = Decimal(0)

            # Calcular costos de tareas a nivel de lote
            for task in tasks:
                labor_cost, input_cost, machinery_cost = self.repository.get_task_costs(task.id)
                task_total = labor_cost + input_cost + machinery_cost
                total_plot_task_cost += task_total

                task_costs.append(TaskCost(
                    tarea_id=task.id,
                    tarea_nombre=task.nombre,
                    fecha=task.fecha_inicio_estimada,
                    costo_mano_obra=labor_cost,
                    costo_insumos=input_cost,
                    costo_maquinaria=machinery_cost,
                    costo_total=task_total,
                    observaciones=task.descripcion
                ))

            # Obtener y procesar cultivos
            crops = self.repository.get_plot_crops_in_period(plot.id, start_date, end_date)
            if crop_id:
                crops = [c for c in crops if c.id == crop_id]

            crop_financials = []
            total_plot_crop_cost = Decimal(0)
            total_plot_income = Decimal(0)

            for crop in crops:
                crop_income = crop.ingreso_total or Decimal(0)
                crop_production_cost = crop.costo_produccion or Decimal(0)
                total_plot_crop_cost += crop_production_cost
                total_plot_income += crop_income

                crop_financials.append(CropFinancials(
                    cultivo_id=crop.id,
                    variedad_maiz=crop.variedad_maiz.nombre,
                    fecha_siembra=crop.fecha_siembra,
                    fecha_cosecha=crop.fecha_cosecha,
                    produccion_total=crop.produccion_total,
                    cantidad_vendida=crop.cantidad_vendida,
                    precio_venta_unitario=crop.precio_venta_unitario,
                    ingreso_total=crop_income,
                    costo_produccion=crop_production_cost,
                    costo_total=crop_production_cost,
                    ganancia_neta=crop_income - crop_production_cost
                ))

            # Calcular totales del lote
            total_plot_cost = total_plot_task_cost + total_plot_crop_cost

            plot_financials.append(PlotFinancials(
                lote_id=plot.id,
                lote_nombre=plot.nombre,
                cultivos=crop_financials,
                tareas=task_costs,  # Agregar las tareas a nivel de lote
                costo_tareas=total_plot_task_cost,  # Nuevo campo
                costo_cultivos=total_plot_crop_cost,  # Nuevo campo
                costo_total=total_plot_cost,
                ingreso_total=total_plot_income,
                ganancia_neta=total_plot_income - total_plot_cost
            ))

            total_farm_cost += total_plot_cost
            total_farm_income += total_plot_income

        return FarmFinancialReport(
            finca_id=farm.id,
            finca_nombre=farm.nombre,
            fecha_inicio=start_date,
            fecha_fin=end_date,
            lotes=plot_financials,
            costo_total=total_farm_cost,
            ingreso_total=total_farm_income,
            ganancia_neta=total_farm_income - total_farm_cost
        )