from decimal import Decimal
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
        
class TareaLaborCulturalBase(BaseModel):
    tipo_labor_id: int
    fecha_programada: date
    descripcion: Optional[str] = Field(None, max_length=500)
    costo_mano_obra: Decimal = Field(..., ge=0, decimal_places=2)
    estado_id: int
    observaciones: Optional[str] = None
    fecha_completada: Optional[date] = None

class TareaLaborCulturalCreate(TareaLaborCulturalBase):
    pass

class TareaLaborCulturalResponse(TareaLaborCulturalBase):
    id: int

    class Config:
        from_attributes = True

class AssignmentCreate(BaseModel):
    usuario_id: int
    tarea_labor_cultural_id: int
    lote_id: int
    estado_id: int
    notas: Optional[str] = None

class AssignmentResponse(BaseModel):
    id: int
    usuario_id: int
    tarea_labor_cultural_id: int
    lote_id: int
    fecha_asignacion: datetime
    estado_id: int
    notas: Optional[str]
    fecha_modificacion: Optional[datetime]

    class Config:
        from_attributes = True