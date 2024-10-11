from decimal import Decimal
from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional
        
class CulturalTaskBase(BaseModel):
    tipo_labor_id: int
    lote_id: int
    fecha_programada: date
    descripcion: Optional[str] = Field(None, max_length=500)
    costo_mano_obra: Decimal = Field(..., ge=0, decimal_places=2)
    estado_id: int
    observaciones: Optional[str] = None
    fecha_completada: Optional[date] = None

class CulturalTaskCreate(CulturalTaskBase):
    pass

class AssignmentCreate(BaseModel):
    usuario_ids: List[int]
    tarea_labor_cultural_id: int
    notas: Optional[str] = None
    
class AssignmentCreateSingle(BaseModel):
    usuario_id: int
    tarea_labor_cultural_id: int
    notas: Optional[str] = None

class AssignmentResponse(BaseModel):
    usuario_id: int
    tarea_labor_cultural_id: int
    notas: Optional[str]

    class Config:
        from_attributes = True
        
class PaginatedAssignmentListResponse(BaseModel):
    assignments: List[AssignmentResponse]
    total_assignments: int
    page: int
    per_page: int
    total_pages: int