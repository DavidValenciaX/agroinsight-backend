# app/reports/application/generate_financial_report_use_case.py
from datetime import date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.reports.infrastructure.sql_repository import FinancialReportRepository
from app.farm.application.services.farm_service import FarmService
from app.reports.domain.schemas import FarmFinancialReport, PlotFinancials, CropFinancials, TaskCost
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

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
        min_cost: Optional[float] = None,
        max_cost: Optional[float] = None,
        task_types: Optional[List[str]] = None,
        group_by: str = "none",
        only_profitable: Optional[bool] = None,
        current_user: UserInDB = None
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

        # Obtener la moneda por defecto (COP)
        default_currency = self.repository.get_default_currency()
        if not default_currency:
            raise DomainException(
                message="No se pudo obtener la moneda por defecto",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        plots = self.repository.get_farm_plots(farm_id)
        if plot_id:
            plots = [p for p in plots if p.id == plot_id]

        plot_financials = []
        total_farm_cost = Decimal(0)
        total_farm_income = Decimal(0)

        # Aplicar filtros de costo a las tareas
        def filter_task_costs(tasks: List[TaskCost]) -> List[TaskCost]:
            filtered = tasks
            if min_cost is not None:
                filtered = [t for t in filtered if t.costo_total >= min_cost]
            if max_cost is not None:
                filtered = [t for t in filtered if t.costo_total <= max_cost]
            if task_types:
                print("Tipos de tarea disponibles:", [t.tipo_labor_nombre for t in tasks])
                print("Tipos de tarea para filtrar:", task_types)
                filtered = [t for t in filtered if t.tipo_labor_nombre in task_types]
            return filtered

        # Aplicar filtros a los cultivos
        def filter_crops(crops: List[CropFinancials]) -> List[CropFinancials]:
            filtered = crops
            if only_profitable is not None:
                filtered = [c for c in filtered if (c.ganancia_neta or 0) > 0 == only_profitable]
            return filtered

        for plot in plots:
            # Obtener tareas a nivel de LOTE
            plot_tasks = self.repository.get_plot_level_tasks_in_period(plot.id, start_date, end_date)
            plot_task_costs = []
            total_plot_task_cost = Decimal(0)

            for task in plot_tasks:
                labor_cost, input_cost, machinery_cost = self.repository.get_task_costs(task.id)
                task_total = labor_cost + input_cost + machinery_cost
                total_plot_task_cost += task_total

                plot_task_costs.append(TaskCost(
                    tarea_id=task.id,
                    tarea_nombre=task.nombre,
                    tipo_labor_nombre=task.tipo_labor.nombre,
                    nivel="LOTE",
                    fecha=task.fecha_inicio_estimada,
                    costo_mano_obra=labor_cost,
                    costo_insumos=input_cost,
                    costo_maquinaria=machinery_cost,
                    costo_total=task_total,
                    observaciones=task.descripcion
                ))

            # Filtrar tareas del lote según los criterios
            plot_task_costs = filter_task_costs(plot_task_costs)
            total_plot_task_cost = sum(task.costo_total for task in plot_task_costs)

            # Obtener y procesar cultivos
            crops = self.repository.get_plot_crops_in_period(plot.id, start_date, end_date)
            if crop_id:
                crops = [c for c in crops if c.id == crop_id]

            crop_financials = []
            total_plot_crop_cost = Decimal(0)
            total_plot_income = Decimal(0)

            for crop in crops:
                # Obtener tareas a nivel de CULTIVO
                crop_tasks = self.repository.get_crop_level_tasks_in_period(crop.id, start_date, end_date)
                crop_task_costs = []
                total_crop_task_cost = Decimal(0)

                for task in crop_tasks:
                    labor_cost, input_cost, machinery_cost = self.repository.get_task_costs(task.id)
                    task_total = labor_cost + input_cost + machinery_cost
                    total_crop_task_cost += task_total

                    crop_task_costs.append(TaskCost(
                        tarea_id=task.id,
                        tarea_nombre=task.nombre,
                        tipo_labor_nombre=task.tipo_labor.nombre,
                        nivel="CULTIVO",
                        fecha=task.fecha_inicio_estimada,
                        costo_mano_obra=labor_cost,
                        costo_insumos=input_cost,
                        costo_maquinaria=machinery_cost,
                        costo_total=task_total,
                        observaciones=task.descripcion
                    ))

                # Filtrar tareas del cultivo según los criterios
                crop_task_costs = filter_task_costs(crop_task_costs)
                total_crop_task_cost = sum(task.costo_total for task in crop_task_costs)

                crop_income = crop.ingreso_total or Decimal(0)
                crop_production_cost = (crop.costo_produccion or Decimal(0)) + total_crop_task_cost
                total_plot_crop_cost += crop_production_cost
                total_plot_income += crop_income

                crop_financials.append(CropFinancials(
                    cultivo_id=crop.id,
                    variedad_maiz=crop.variedad_maiz.nombre,
                    fecha_siembra=crop.fecha_siembra,
                    fecha_cosecha=crop.fecha_cosecha,
                    produccion_total=crop.produccion_total,
                    produccion_total_unidad_id=crop.produccion_total_unidad_id,
                    produccion_total_unidad_simbolo=crop.produccion_total_unidad.abreviatura if crop.produccion_total_unidad else None,
                    cantidad_vendida=crop.cantidad_vendida,
                    cantidad_vendida_unidad_id=crop.cantidad_vendida_unidad_id,
                    cantidad_vendida_unidad_simbolo=crop.cantidad_vendida_unidad.abreviatura if crop.cantidad_vendida_unidad else None,
                    precio_venta_unitario=crop.precio_venta_unitario,
                    moneda_id=crop.moneda_id,
                    moneda_simbolo=crop.moneda.abreviatura if crop.moneda else None,
                    ingreso_total=crop_income,
                    costo_produccion=crop.costo_produccion,
                    tareas_cultivo=crop_task_costs,
                    costo_total=crop_production_cost,
                    ganancia_neta=crop_income - crop_production_cost
                ))

            # Filtrar cultivos según criterios
            crop_financials = filter_crops(crop_financials)
            total_plot_crop_cost = sum(crop.costo_total for crop in crop_financials)
            total_plot_income = sum(crop.ingreso_total or 0 for crop in crop_financials)

            # Si se especificó group_by, agrupar las tareas
            if group_by != "none":
                plot_task_costs = self._group_tasks(plot_task_costs, group_by)
                for crop in crop_financials:
                    crop.tareas_cultivo = self._group_tasks(crop.tareas_cultivo, group_by)

            # Calcular totales del lote
            total_plot_cost = total_plot_task_cost + total_plot_crop_cost + plot.costos_mantenimiento

            plot_financials.append(PlotFinancials(
                lote_id=plot.id,
                lote_nombre=plot.nombre,
                cultivos=crop_financials,
                tareas_lote=plot_task_costs,
                costo_mantenimiento_base=plot.costos_mantenimiento,
                costo_tareas=total_plot_task_cost,
                costo_cultivos=total_plot_crop_cost,
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
            moneda=default_currency.nombre,
            lotes=plot_financials,
            costo_total=total_farm_cost,
            ingreso_total=total_farm_income,
            ganancia_neta=total_farm_income - total_farm_cost
        )

    def _group_tasks(self, tasks: List[TaskCost], group_by: str) -> List[TaskCost]:
        """Agrupa las tareas según el criterio especificado"""
        if group_by == "task_type":
            # Agrupar por tipo de tarea
            grouped = {}
            for task in tasks:
                if task.tarea_nombre not in grouped:
                    grouped[task.tarea_nombre] = {
                        'costo_mano_obra': Decimal(0),
                        'costo_insumos': Decimal(0),
                        'costo_maquinaria': Decimal(0),
                        'costo_total': Decimal(0)
                    }
                grouped[task.tarea_nombre]['costo_mano_obra'] += task.costo_mano_obra
                grouped[task.tarea_nombre]['costo_insumos'] += task.costo_insumos
                grouped[task.tarea_nombre]['costo_maquinaria'] += task.costo_maquinaria
                grouped[task.tarea_nombre]['costo_total'] += task.costo_total

            return [
                TaskCost(
                    tarea_id=-1,  # ID genérico para grupos
                    tarea_nombre=name,
                    fecha=date.today(),  # Fecha representativa
                    nivel="AGRUPADO",
                    **costs
                ) for name, costs in grouped.items()
            ]
        
        elif group_by == "month":
            # Agrupar por mes
            grouped = {}
            for task in tasks:
                month_key = task.fecha.strftime("%Y-%m")  # Formato: "2024-03"
                if month_key not in grouped:
                    grouped[month_key] = {
                        'costo_mano_obra': Decimal(0),
                        'costo_insumos': Decimal(0),
                        'costo_maquinaria': Decimal(0),
                        'costo_total': Decimal(0)
                    }
                grouped[month_key]['costo_mano_obra'] += task.costo_mano_obra
                grouped[month_key]['costo_insumos'] += task.costo_insumos
                grouped[month_key]['costo_maquinaria'] += task.costo_maquinaria
                grouped[month_key]['costo_total'] += task.costo_total

            return [
                TaskCost(
                    tarea_id=-1,  # ID genérico para grupos
                    tarea_nombre=f"Tareas de {month_key}",
                    tipo_labor_nombre="Agrupación Mensual",
                    fecha=date.fromisoformat(f"{month_key}-01"),  # Primer día del mes
                    nivel="AGRUPADO",
                    observaciones=f"Tareas agrupadas del mes {month_key}",
                    **costs
                ) for month_key, costs in grouped.items()
            ]
        
        elif group_by == "cost_type":
            # Agrupar por tipo de costo
            total_by_type = {
                'Mano de Obra': Decimal(0),
                'Insumos': Decimal(0),
                'Maquinaria': Decimal(0)
            }
            
            for task in tasks:
                total_by_type['Mano de Obra'] += task.costo_mano_obra
                total_by_type['Insumos'] += task.costo_insumos
                total_by_type['Maquinaria'] += task.costo_maquinaria

            return [
                TaskCost(
                    tarea_id=-1,
                    tarea_nombre=cost_type,
                    tipo_labor_nombre="Agrupación por Tipo de Costo",
                    fecha=date.today(),
                    nivel="AGRUPADO",
                    costo_mano_obra=total if cost_type == 'Mano de Obra' else Decimal(0),
                    costo_insumos=total if cost_type == 'Insumos' else Decimal(0),
                    costo_maquinaria=total if cost_type == 'Maquinaria' else Decimal(0),
                    costo_total=total,
                    observaciones=f"Total de costos de {cost_type}"
                ) for cost_type, total in total_by_type.items() if total > 0
            ]

        # Si no hay agrupación o no se reconoce el tipo
        return tasks