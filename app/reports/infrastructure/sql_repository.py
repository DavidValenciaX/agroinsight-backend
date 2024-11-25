# app/reports/infrastructure/sql_repository.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from datetime import date
from typing import List, Optional
from app.crop.infrastructure.orm_models import Crop
from app.cultural_practices.infrastructure.orm_models import CulturalTask, CulturalTaskType, NivelLaborCultural
from app.measurement.application.services.measurement_service import MeasurementService
from app.plot.infrastructure.orm_models import Plot
from app.measurement.infrastructure.orm_models import UnitOfMeasure, UnitCategory

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
                CulturalTask.fecha_inicio_estimada <= end_date,
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
                CulturalTask.fecha_inicio_estimada <= end_date,
                CulturalTaskType.nivel == NivelLaborCultural.CULTIVO,
                CulturalTask.fecha_inicio_estimada >= crop.fecha_siembra,
                or_(
                    (crop.fecha_cosecha == None),
                    (CulturalTask.fecha_inicio_estimada <= crop.fecha_cosecha)
                )
            ).all()