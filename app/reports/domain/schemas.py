# app/reports/domain/schemas.py
from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from typing import List, Optional

class TaskCost(BaseModel):
    """Costos asociados a una tarea específica"""
    tarea_id: int
    tarea_nombre: str
    fecha: date
    costo_mano_obra: Decimal
    costo_insumos: Decimal
    costo_maquinaria: Decimal
    costo_total: Decimal
    observaciones: Optional[str]

class CropFinancials(BaseModel):
    """Información financiera de un cultivo"""
    cultivo_id: int
    variedad_maiz: str
    fecha_siembra: date
    fecha_cosecha: Optional[date]
    produccion_total: Optional[int]
    cantidad_vendida: Optional[int]
    precio_venta_unitario: Optional[Decimal]
    ingreso_total: Optional[Decimal]
    costo_produccion: Optional[Decimal]
    costos_tareas: List[TaskCost]
    costo_total: Decimal
    ganancia_neta: Optional[Decimal]

class PlotFinancials(BaseModel):
    """Información financiera de un lote"""
    lote_id: int
    lote_nombre: str
    cultivos: List[CropFinancials]
    tareas: List[TaskCost]
    costo_tareas: Decimal
    costo_cultivos: Decimal
    costo_total: Decimal
    ingreso_total: Decimal
    ganancia_neta: Decimal

class FarmFinancialReport(BaseModel):
    """Reporte financiero completo de una finca"""
    finca_id: int
    finca_nombre: str
    fecha_inicio: date
    fecha_fin: date
    lotes: List[PlotFinancials]
    costo_total: Decimal
    ingreso_total: Decimal
    ganancia_neta: Decimal