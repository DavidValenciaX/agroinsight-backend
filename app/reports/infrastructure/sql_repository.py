# app/reports/infrastructure/sql_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import List, Tuple
from decimal import Decimal

from app.costs.infrastructure.orm_models import LaborCost, TaskInput, TaskMachinery
from app.crop.infrastructure.orm_models import Crop
from app.cultural_practices.infrastructure.orm_models import CulturalTask
from app.plot.infrastructure.orm_models import Plot

class FinancialReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_task_costs(self, task_id: int) -> Tuple[Decimal, Decimal, Decimal]:
        """Obtiene los costos de una tarea específica"""
        # Costo mano de obra
        labor_cost = self.db.query(func.coalesce(func.sum(LaborCost.costo_total), 0))\
            .filter(LaborCost.tarea_labor_id == task_id)\
            .scalar()

        # Costo insumos
        input_cost = self.db.query(func.coalesce(func.sum(TaskInput.costo_total), 0))\
            .filter(TaskInput.tarea_labor_id == task_id)\
            .scalar()

        # Costo maquinaria
        machinery_cost = self.db.query(func.coalesce(func.sum(TaskMachinery.costo_total), 0))\
            .filter(TaskMachinery.tarea_labor_id == task_id)\
            .scalar()

        return labor_cost, input_cost, machinery_cost

    def get_plot_tasks_in_period(self, plot_id: int, start_date: date, end_date: date) -> List[CulturalTask]:
        """Obtiene todas las tareas de un lote en un período específico"""
        return self.db.query(CulturalTask)\
            .filter(
                CulturalTask.lote_id == plot_id,
                CulturalTask.fecha_inicio_estimada >= start_date,
                CulturalTask.fecha_inicio_estimada <= end_date
            ).all()

    def get_plot_crops_in_period(self, plot_id: int, start_date: date, end_date: date) -> List[Crop]:
        """Obtiene todos los cultivos de un lote en un período específico"""
        return self.db.query(Crop)\
            .filter(
                Crop.lote_id == plot_id,
                Crop.fecha_siembra >= start_date,
                Crop.fecha_siembra <= end_date
            ).all()

    def get_farm_plots(self, farm_id: int) -> List[Plot]:
        """Obtiene todos los lotes de una finca"""
        return self.db.query(Plot)\
            .filter(Plot.finca_id == farm_id)\
            .all()