from pydantic import BaseModel
from datetime import datetime
from typing import Optional

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