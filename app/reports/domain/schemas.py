# app/reports/domain/schemas.py
from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from typing import List, Optional

class TaskCost(BaseModel):
    """Costos asociados a una tarea específica"""
    tarea_id: int
    tarea_nombre: str
    tipo_labor_nombre: str
    fecha_inicio: date
    fecha_finalizacion: date
    nivel: str
    estado_id: int
    estado_nombre: str
    cantidad_trabajadores: int
    horas_trabajadas: int
    costo_hora_trabajador: Decimal
    costo_mano_obra: Decimal
    insumo: str
    cantidad_insumos: int
    unidad_insumos: str
    precio_unitario_insumos: Decimal
    costo_insumos: Decimal
    maquinaria: str
    horas_maquinaria: int
    precio_hora_maquinaria: Decimal
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
    produccion_total_unidad_id: Optional[int]
    produccion_total_unidad_simbolo: Optional[str]
    cantidad_vendida: Optional[int]
    cantidad_vendida_unidad_id: Optional[int]
    cantidad_vendida_unidad_simbolo: Optional[str]
    precio_venta_unitario: Optional[Decimal]
    moneda_id: Optional[int]
    moneda_simbolo: Optional[str]
    ingreso_total: Decimal
    costo_produccion: Decimal
    tareas_cultivo: List[TaskCost]
    ganancia_neta: Decimal

class PlotFinancials(BaseModel):
    """Información financiera de un lote"""
    lote_id: int
    lote_nombre: str
    cultivos: List[CropFinancials]
    tareas_lote: List[TaskCost]
    costo_mantenimiento: Decimal
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
    moneda_simbolo: str
    lotes: List[PlotFinancials]
    costo_total: Decimal
    ingreso_total: Decimal
    ganancia_neta: Decimal