# app/reports/infrastructure/sql_repository.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from datetime import date
from typing import List, Optional
from app.crop.infrastructure.orm_models import Crop
from app.cultural_practices.infrastructure.orm_models import CulturalTask, CulturalTaskType, NivelLaborCultural
from app.measurement.application.services.measurement_service import MeasurementService
from app.plot.infrastructure.orm_models import Plot
from app.measurement.infrastructure.orm_models import UnitOfMeasure, UnitCategory
from app.costs.infrastructure.orm_models import TaskMachinery, AgriculturalMachinery, MachineryType, TaskInput, AgriculturalInput, AgriculturalInputCategory

class FinancialReportRepository:
    def __init__(self, db: Session):
        self.db = db
        self.measurement_service = MeasurementService(db)

    def get_plot_tasks_in_period(self, plot_id: int, start_date: date, end_date: date) -> List[CulturalTask]:
        """Obtiene todas las tareas de un lote en un período específico"""
        return self.db.query(CulturalTask)\
            .filter(
                CulturalTask.lote_id == plot_id,
                CulturalTask.fecha_inicio_estimada >= start_date,
                CulturalTask.fecha_inicio_estimada <= end_date
            ).all()

    def get_plot_crops_in_period(self, plot_id: int, start_date: date, end_date: date) -> List[Crop]:
        """Obtiene todos los cultivos de un lote en un período específico."""
        return self.db.query(Crop)\
            .options(joinedload(Crop.variedad_maiz))\
            .options(joinedload(Crop.produccion_total_unidad))\
            .options(joinedload(Crop.cantidad_vendida_unidad))\
            .options(joinedload(Crop.moneda))\
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

    def get_plot_level_tasks_in_period(self, plot_id: int, start_date: date, end_date: date) -> List[CulturalTask]:
        """Obtiene las tareas de nivel LOTE en un período específico"""
        return self.db.query(CulturalTask)\
            .options(joinedload(CulturalTask.tipo_labor))\
            .join(CulturalTaskType)\
            .filter(
                CulturalTask.lote_id == plot_id,
                CulturalTask.fecha_inicio_estimada >= start_date,
                CulturalTask.fecha_finalizacion <= end_date,
                CulturalTaskType.nivel == NivelLaborCultural.LOTE
            ).all()

    def get_crop_level_tasks_in_period(self, crop_id: int, start_date: date, end_date: date) -> List[CulturalTask]:
        """Obtiene las tareas de nivel CULTIVO en un período específico para un cultivo"""
        # Primero obtenemos el cultivo para saber su lote
        crop = self.db.query(Crop).filter(Crop.id == crop_id).first()
        if not crop:
            return []
        
        return self.db.query(CulturalTask)\
            .options(joinedload(CulturalTask.tipo_labor))\
            .join(CulturalTaskType)\
            .filter(
                CulturalTask.lote_id == crop.lote_id,
                CulturalTask.fecha_inicio_estimada >= start_date,
                CulturalTask.fecha_finalizacion <= end_date,
                CulturalTaskType.nivel == NivelLaborCultural.CULTIVO
            ).all()

    def get_top_machinery_usage(self, farm_id: int, start_date: date, end_date: date, limit: int = 10) -> List[tuple]:
        """Obtiene el top de maquinaria más usada en una finca durante un período.

        Args:
            farm_id: ID de la finca
            start_date: Fecha de inicio del período
            end_date: Fecha fin del período
            limit: Cantidad de registros a retornar (default 10)

        Returns:
            List[tuple]: Lista de tuplas con (maquinaria_id, nombre, tipo_nombre, horas_uso, costo_total)
        """
        return self.db.query(
            TaskMachinery.maquinaria_id,
            AgriculturalMachinery.nombre,
            MachineryType.nombre.label('tipo_nombre'),
            func.sum(TaskMachinery.horas_uso).label('total_horas_uso'),
            func.sum(TaskMachinery.horas_uso * AgriculturalMachinery.costo_hora).label('costo_total')
        ).join(
            AgriculturalMachinery,
            TaskMachinery.maquinaria_id == AgriculturalMachinery.id
        ).join(
            MachineryType,
            AgriculturalMachinery.tipo_maquinaria_id == MachineryType.id
        ).join(
            CulturalTask,
            TaskMachinery.tarea_labor_id == CulturalTask.id
        ).join(
            Plot,
            CulturalTask.lote_id == Plot.id
        ).filter(
            Plot.finca_id == farm_id,
            TaskMachinery.fecha_uso >= start_date,
            TaskMachinery.fecha_uso <= end_date
        ).group_by(
            TaskMachinery.maquinaria_id,
            AgriculturalMachinery.nombre,
            MachineryType.nombre
        ).order_by(
            func.sum(TaskMachinery.horas_uso).desc()
        ).limit(limit).all()

    def get_top_input_usage(self, farm_id: int, start_date: date, end_date: date, limit: int = 10) -> List[tuple]:
        """Obtiene el top de insumos más usados en una finca durante un período.

        Args:
            farm_id: ID de la finca
            start_date: Fecha de inicio del período
            end_date: Fecha fin del período
            limit: Cantidad de registros a retornar (default 10)

        Returns:
            List[tuple]: Lista de tuplas con (insumo_id, nombre, categoria_nombre, unidad_medida_simbolo, cantidad_total, costo_total)
        """
        return self.db.query(
            TaskInput.insumo_id,
            AgriculturalInput.nombre,
            AgriculturalInputCategory.nombre.label('categoria_nombre'),
            UnitOfMeasure.abreviatura.label('unidad_medida_simbolo'),
            func.sum(TaskInput.cantidad_utilizada).label('cantidad_total'),
            func.sum(TaskInput.cantidad_utilizada * AgriculturalInput.costo_unitario).label('costo_total')
        ).join(
            AgriculturalInput,
            TaskInput.insumo_id == AgriculturalInput.id
        ).join(
            AgriculturalInputCategory,
            AgriculturalInput.categoria_id == AgriculturalInputCategory.id
        ).join(
            UnitOfMeasure,
            AgriculturalInput.unidad_medida_id == UnitOfMeasure.id
        ).join(
            CulturalTask,
            TaskInput.tarea_labor_id == CulturalTask.id
        ).join(
            Plot,
            CulturalTask.lote_id == Plot.id
        ).filter(
            Plot.finca_id == farm_id,
            TaskInput.fecha_aplicacion >= start_date,
            TaskInput.fecha_aplicacion <= end_date
        ).group_by(
            TaskInput.insumo_id,
            AgriculturalInput.nombre,
            AgriculturalInputCategory.nombre,
            UnitOfMeasure.abreviatura
        ).order_by(
            func.sum(TaskInput.cantidad_utilizada).desc()
        ).limit(limit).all()