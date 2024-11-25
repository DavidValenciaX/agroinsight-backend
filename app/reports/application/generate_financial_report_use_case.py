# app/reports/application/generate_financial_report_use_case.py
from datetime import date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session
from app.costs.infrastructure.sql_repository import CostsRepository
from app.farm.infrastructure.sql_repository import FarmRepository
from app.measurement.application.services.measurement_service import MeasurementService
from app.measurement.infrastructure.sql_repository import MeasurementRepository
from app.reports.infrastructure.sql_repository import FinancialReportRepository
from app.farm.application.services.farm_service import FarmService
from app.reports.domain.schemas import FarmFinancialReport, PlotFinancials, CropFinancials, TaskCost, GroupedTaskCost, TopMachineryUsage, TopInputUsage
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from app.measurement.application.services.currency_conversion_service import CurrencyConversionService

from app.user.domain.schemas import UserInDB
from app.reports.domain.schemas import InputSchema, MachinerySchema, LaborCostSchema

class GenerateFinancialReportUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.repository = FinancialReportRepository(db)
        self.farm_service = FarmService(db)
        self.farm_repository = FarmRepository(db)
        self.costs_repository = CostsRepository(db)
        self.currency_service = CurrencyConversionService(db)
        self.measurement_repository = MeasurementRepository(db)
        self.measurement_service = MeasurementService(db)
        
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
        currency_id: Optional[int] = None,
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
        default_currency = self.measurement_service.get_default_currency()
        if not default_currency:
            raise DomainException(
                message="No se pudo obtener la moneda por defecto",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Obtener la moneda solicitada o usar COP por defecto
        target_currency = default_currency
        if currency_id:
            target_currency = self.measurement_repository.get_unit_of_measure_by_id(currency_id)
            if not target_currency:
                raise DomainException(
                    message="Moneda no encontrada",
                    status_code=status.HTTP_404_NOT_FOUND
                )

        # Function to convert amounts, with default from_currency
        def convert_amount(amount: Decimal, from_currency: str = default_currency.abreviatura) -> Decimal:
            if not amount:
                return Decimal(0)
            return self.currency_service.convert_amount(
                amount,
                from_currency,
                target_currency.abreviatura
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
                task_cost = self._create_task_cost(task, "LOTE", convert_amount, target_currency)
                plot_task_costs.append(task_cost)

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
                # Calculate income and costs from task data
                crop_income = Decimal(0)
                if crop.cantidad_vendida and crop.precio_venta_unitario:
                    crop_income = Decimal(crop.cantidad_vendida) * Decimal(crop.precio_venta_unitario)

                # Get crop tasks and their costs
                crop_tasks = self.repository.get_crop_level_tasks_in_period(crop.id, start_date, end_date)
                crop_task_costs = []
                total_crop_task_cost = Decimal(0)

                for task in crop_tasks:
                    task_cost = self._create_task_cost(task, "CULTIVO", convert_amount, target_currency)
                    crop_task_costs.append(task_cost)

                # Filtrar tareas del cultivo según los criterios
                crop_task_costs = filter_task_costs(crop_task_costs)
                total_crop_task_cost = sum(task.costo_total for task in crop_task_costs)

                # Update crop financials without using costo_produccion
                crop_financials.append(self._create_crop_financials(crop, crop_task_costs, convert_amount, target_currency))

            # Filtrar cultivos según criterios
            crop_financials = filter_crops(crop_financials)
            total_plot_crop_cost = sum(crop.costo_produccion for crop in crop_financials)
            total_plot_income = sum(crop.ingreso_total or 0 for crop in crop_financials)

            # Si se especificó group_by, agrupar las tareas
            if group_by != "none":
                plot_task_costs = self._group_tasks(plot_task_costs, group_by)
                for crop in crop_financials:
                    crop.tareas_cultivo = self._group_tasks(crop.tareas_cultivo, group_by)

            # Calcular totales del lote
            total_plot_cost = total_plot_task_cost + total_plot_crop_cost

            plot_financials.append(PlotFinancials(
                lote_id=plot.id,
                lote_nombre=plot.nombre,
                cultivos=crop_financials,
                tareas_lote=plot_task_costs,
                costo_mantenimiento=total_plot_task_cost,
                costo_cultivos=total_plot_crop_cost,
                costo_total=total_plot_cost,
                ingreso_total=total_plot_income,
                ganancia_neta=total_plot_income - total_plot_cost
            ))

            total_farm_cost += total_plot_cost
            total_farm_income += total_plot_income

        # Antes del return final, obtener el top de maquinaria
        top_machinery_data = self.repository.get_top_machinery_usage(
            farm_id, 
            start_date, 
            end_date
        )
        
        top_machinery = []
        for m_id, nombre, tipo_nombre, horas_uso, costo in top_machinery_data:
            # Convertir el costo a la moneda objetivo
            costo_convertido = self.currency_service.convert_amount(
                costo,
                default_currency.abreviatura,
                target_currency.abreviatura
            )
            
            top_machinery.append(TopMachineryUsage(
                maquinaria_id=m_id,
                nombre=nombre,
                tipo_maquinaria_nombre=tipo_nombre,
                total_horas_uso=horas_uso,
                costo_total=costo_convertido
            ))

        # Obtener el top de insumos
        top_inputs_data = self.repository.get_top_input_usage(
            farm_id, 
            start_date, 
            end_date
        )

        top_inputs = []
        for i_id, nombre, cat_nombre, um_simbolo, cantidad, costo in top_inputs_data:
            # Convertir el costo a la moneda objetivo
            costo_convertido = self.currency_service.convert_amount(
                costo,
                default_currency.abreviatura,
                target_currency.abreviatura
            )
            
            top_inputs.append(TopInputUsage(
                insumo_id=i_id,
                nombre=nombre,
                categoria_nombre=cat_nombre,
                unidad_medida_simbolo=um_simbolo,
                cantidad_total=cantidad,
                costo_total=costo_convertido
            ))

        return FarmFinancialReport(
            finca_id=farm.id,
            finca_nombre=farm.nombre,
            fecha_inicio=start_date,
            fecha_fin=end_date,
            moneda_simbolo=target_currency.abreviatura,
            lotes=plot_financials,
            costo_total=total_farm_cost,
            ingreso_total=total_farm_income,
            ganancia_neta=total_farm_income - total_farm_cost,
            top_maquinaria=top_machinery,
            top_insumos=top_inputs
        )

    def _group_tasks(self, tasks: List[TaskCost], group_by: str) -> List[GroupedTaskCost]:
        """
        Agrupa las tareas según el criterio especificado.
        Solo se permite un criterio de agrupación a la vez.
        """
        if not tasks:
            return []
        
        if not group_by or group_by == "none":
            return tasks

        if group_by == "task_type":
            # Agrupar por tipo de tarea
            grouped = {}
            for task in tasks:
                if task.tipo_labor_nombre not in grouped:
                    grouped[task.tipo_labor_nombre] = {
                        'costo_mano_obra': Decimal(0),
                        'costo_insumos': Decimal(0),
                        'costo_maquinaria': Decimal(0),
                        'costo_total': Decimal(0)
                    }
                grouped[task.tipo_labor_nombre]['costo_mano_obra'] += task.costo_mano_obra
                grouped[task.tipo_labor_nombre]['costo_insumos'] += task.costo_insumos
                grouped[task.tipo_labor_nombre]['costo_maquinaria'] += task.costo_maquinaria
                grouped[task.tipo_labor_nombre]['costo_total'] += task.costo_total

            return [
                GroupedTaskCost(
                    categoria=name,
                    costo_total=costs['costo_total'],
                    observaciones=f"Total de costos de {name}"
                ) for name, costs in grouped.items()
            ]
        
        elif group_by == "month":
            # Diccionario para mapear números de mes a nombres en español
            meses = {
                "01": "Enero",
                "02": "Febrero",
                "03": "Marzo",
                "04": "Abril",
                "05": "Mayo",
                "06": "Junio",
                "07": "Julio",
                "08": "Agosto",
                "09": "Septiembre",
                "10": "Octubre",
                "11": "Noviembre",
                "12": "Diciembre"
            }
            
            grouped = {}
            for task in tasks:
                # Obtener el año y mes
                year = task.fecha_finalizacion.strftime("%Y")
                month = task.fecha_finalizacion.strftime("%m")
                month_key = task.fecha_finalizacion.strftime("%Y-%m")  # Para mantener el orden
                month_name = f"{meses[month]} {year}"  # Nombre del mes con año
                
                if month_key not in grouped:
                    grouped[month_key] = {
                        'nombre': month_name,  # Guardamos el nombre para usar después
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
                GroupedTaskCost(
                    categoria=f"Tareas de {costs['nombre']}",
                    costo_total=costs['costo_total'],
                    observaciones=f"Tareas agrupadas del mes de {costs['nombre']}"
                ) for costs in grouped.values()
            ]
        
        elif group_by == "cost_type":
            # Agrupar por tipo de costo
            total_by_type = {
                'Mano de Obra': Decimal(0),
                'Insumos': Decimal(0),
                'Maquinaria': Decimal(0)
            }
            
            for task in tasks:
                total_by_type['Mano de Obra'] += task.costo_mano_obra or Decimal(0)
                total_by_type['Insumos'] += task.costo_insumos or Decimal(0)
                total_by_type['Maquinaria'] += task.costo_maquinaria or Decimal(0)

            grouped_tasks = []
            for cost_type, total in total_by_type.items():
                if total > 0:
                    grouped_task = GroupedTaskCost(
                        categoria=cost_type,
                        costo_total=total,
                        observaciones=f"Total de costos para {cost_type}"
                    )
                    grouped_tasks.append(grouped_task)

            return grouped_tasks

        # Si no hay agrupación o no se reconoce el tipo
        return tasks

    def _create_task_cost(self, task, nivel: str, convert_amount_func, target_currency) -> TaskCost:
        """Helper method to create TaskCost with converted currency values"""
        # Get costs
        labor_cost, input_cost, machinery_cost = self.costs_repository.get_task_costs(task.id)
        # Convert costs to target currency
        labor_cost = convert_amount_func(labor_cost)
        input_cost = convert_amount_func(input_cost)
        machinery_cost = convert_amount_func(machinery_cost)
        task_total = labor_cost + input_cost + machinery_cost

        return TaskCost(
            tarea_id=task.id,
            tarea_nombre=task.nombre,
            tipo_labor_nombre=task.tipo_labor.nombre,
            nivel=nivel,
            fecha_inicio=task.fecha_inicio_estimada,
            fecha_finalizacion=task.fecha_finalizacion,
            estado_id=task.estado_id,
            estado_nombre=task.estado.nombre,
            mano_obra=LaborCostSchema(
                cantidad_trabajadores=task.costo_mano_obra.cantidad_trabajadores,
                horas_trabajadas=task.costo_mano_obra.horas_trabajadas,
                costo_hora=convert_amount_func(task.costo_mano_obra.costo_hora),
                moneda_id=target_currency.id,
                moneda_simbolo=target_currency.abreviatura,
                observaciones=task.costo_mano_obra.observaciones
            ) if task.costo_mano_obra else None,
            costo_mano_obra=labor_cost,
            insumos=[
                InputSchema(
                    id=ti.insumo.id,
                    categoria_id=ti.insumo.categoria_id,
                    categoria_nombre=ti.insumo.categoria.nombre,
                    nombre=ti.insumo.nombre,
                    descripcion=ti.insumo.descripcion,
                    unidad_medida_id=ti.insumo.unidad_medida_id,
                    unidad_medida_nombre=ti.insumo.unidad_medida.nombre,
                    costo_unitario=convert_amount_func(ti.insumo.costo_unitario),
                    moneda_id=target_currency.id,
                    moneda_simbolo=target_currency.abreviatura,
                    stock_actual=ti.insumo.stock_actual,
                    cantidad_utilizada=ti.cantidad_utilizada,
                    fecha_aplicacion=ti.fecha_aplicacion,
                    observaciones=ti.observaciones
                ) for ti in task.insumos
            ],
            costo_insumos=input_cost,
            maquinarias=[
                MachinerySchema(
                    id=tm.maquinaria.id,
                    tipo_maquinaria_id=tm.maquinaria.tipo_maquinaria_id,
                    tipo_maquinaria_nombre=tm.maquinaria.tipo_maquinaria.nombre,
                    nombre=tm.maquinaria.nombre,
                    descripcion=tm.maquinaria.descripcion,
                    modelo=tm.maquinaria.modelo,
                    numero_serie=tm.maquinaria.numero_serie,
                    costo_hora=convert_amount_func(tm.maquinaria.costo_hora),
                    moneda_id=target_currency.id,
                    moneda_simbolo=target_currency.abreviatura,
                    horas_uso=tm.horas_uso,
                    fecha_uso=tm.fecha_uso,
                    observaciones=tm.observaciones
                ) for tm in task.maquinarias
            ],
            costo_maquinaria=machinery_cost,
            costo_total=task_total,
            observaciones=task.descripcion
        )

    def _create_crop_financials(self, crop, crop_task_costs, convert_amount_func, target_currency) -> CropFinancials:
        """Helper method to create CropFinancials with converted currency values"""
        # Convert crop income
        crop_income = Decimal(0)
        if crop.cantidad_vendida and crop.precio_venta_unitario:
            precio_venta_convertido = convert_amount_func(crop.precio_venta_unitario)
            crop_income = Decimal(crop.cantidad_vendida) * precio_venta_convertido

        total_crop_task_cost = sum(task.costo_total for task in crop_task_costs)

        return CropFinancials(
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
            precio_venta_unitario=convert_amount_func(crop.precio_venta_unitario) if crop.precio_venta_unitario else None,
            moneda_id=target_currency.id,
            moneda_simbolo=target_currency.abreviatura,
            ingreso_total=crop_income,
            costo_produccion=total_crop_task_cost,
            tareas_cultivo=crop_task_costs,
            ganancia_neta=crop_income - total_crop_task_cost
        )