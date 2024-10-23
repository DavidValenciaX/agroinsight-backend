from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from typing import List, Optional
from decimal import Decimal

class CropCreate(BaseModel):
    lote_id: int = Field(..., gt=0)
    variedad_maiz_id: int = Field(..., gt=0)
    fecha_siembra: date
    densidad_siembra: int = Field(..., gt=0)
    densidad_siembra_unidad_id: int = Field(..., gt=0)
    estado_id: int = Field(..., gt=0)

class CropResponse(BaseModel):
    id: int
    lote_id: int
    variedad_maiz_id: int
    fecha_siembra: date
    densidad_siembra: int
    densidad_siembra_unidad_id: int
    estado_id: int
    fecha_cosecha: Optional[date]
    produccion_total: Optional[int]
    produccion_total_unidad_id: Optional[int]
    precio_venta_unitario: Optional[Decimal]
    cantidad_vendida: Optional[int]
    cantidad_vendida_unidad_id: Optional[int]
    ingreso_total: Optional[Decimal]
    costo_produccion: Optional[Decimal]
    moneda_id: Optional[int]
    fecha_venta: Optional[date]
    fecha_creacion: date
    fecha_modificacion: Optional[date]

    model_config = ConfigDict(from_attributes=True)

class PaginatedCropListResponse(BaseModel):
    crops: List[CropResponse]
    total_crops: int
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1, le=100)
    total_pages: int

