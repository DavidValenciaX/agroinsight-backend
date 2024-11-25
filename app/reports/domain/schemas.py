# app/reports/domain/schemas.py
from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from typing import List, Optional, Union

class InputSchema(BaseModel):
    """Esquema para insumos agrícolas"""
    id: int
    categoria_id: int
    categoria_nombre: str
    nombre: str
    descripcion: Optional[str]
    unidad_medida_id: int
    unidad_medida_nombre: str
    costo_unitario: Decimal
    moneda_id: int
    moneda_simbolo: str
    stock_actual: Decimal
    cantidad_utilizada: Decimal
    fecha_aplicacion: Optional[date]
    observaciones: Optional[str]

    class Config:
        from_attributes = True

class MachinerySchema(BaseModel):
    """Esquema para maquinaria agrícola"""
    id: int
    tipo_maquinaria_id: int
    tipo_maquinaria_nombre: str
    nombre: str
    descripcion: Optional[str]
    modelo: Optional[str]
    numero_serie: Optional[str]
    costo_hora: Decimal
    moneda_id: int
    moneda_simbolo: str
    horas_uso: Decimal
    fecha_uso: Optional[date]
    observaciones: Optional[str]

    class Config:
        from_attributes = True

class LaborCostSchema(BaseModel):
    """Esquema para costos de mano de obra"""
    cantidad_trabajadores: int
    horas_trabajadas: Decimal
    costo_hora: Decimal
    moneda_id: int
    moneda_simbolo: str
    observaciones: Optional[str]

    class Config:
        from_attributes = True

class TaskCost(BaseModel):
    """Costos asociados a una tarea específica"""
    tarea_id: int
    tarea_nombre: str
    tipo_labor_nombre: str
    fecha_inicio: date
    fecha_finalizacion: Optional[date]
    nivel: str
    estado_id: int
    estado_nombre: str
    mano_obra: Optional[LaborCostSchema]
    costo_mano_obra: Decimal
    insumos: Optional[List[InputSchema]]
    costo_insumos: Decimal
    maquinarias: Optional[List[MachinerySchema]]
    costo_maquinaria: Decimal
    costo_total: Decimal
    observaciones: Optional[str]

    class Config:
        from_attributes = True
        
class GroupedTaskCost(BaseModel):
    """Esquema para tareas agrupadas por tipo de costo"""
    categoria: str  # 'Mano de Obra', 'Insumos', 'Maquinaria'
    costo_total: Decimal
    observaciones: Optional[str]

    class Config:
        from_attributes = True

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
    tareas_cultivo: List[Union[TaskCost, GroupedTaskCost]]
    ganancia_neta: Decimal

class PlotFinancials(BaseModel):
    """Información financiera de un lote"""
    lote_id: int
    lote_nombre: str
    cultivos: List[CropFinancials]
    tareas_lote: List[Union[TaskCost, GroupedTaskCost]]
    costo_mantenimiento: Decimal
    costo_cultivos: Decimal
    costo_total: Decimal
    ingreso_total: Decimal
    ganancia_neta: Decimal

class TopMachineryUsage(BaseModel):
    """Información de uso de maquinaria agrícola"""
    maquinaria_id: int
    nombre: str
    tipo_maquinaria_nombre: str
    total_horas_uso: Decimal
    costo_total: Decimal

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
    top_maquinaria: List[TopMachineryUsage]