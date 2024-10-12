from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional
        
class CulturalTaskBase(BaseModel):
    tipo_labor_id: int
    lote_id: int
    fecha_inicio_estimada: date
    descripcion: Optional[str] = Field(None, max_length=500)
    estado_id: int
    fecha_finalizacion: Optional[date] = None
    nombre: str = Field(..., max_length=255)

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