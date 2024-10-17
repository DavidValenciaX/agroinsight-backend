from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional
        
class TaskBase(BaseModel):
    tipo_labor_id: int
    lote_id: int
    fecha_inicio_estimada: date
    descripcion: Optional[str] = Field(None, max_length=500)
    estado_id: int
    nombre: str = Field(..., max_length=255)

class TaskCreate(TaskBase):
    pass

class SuccessTaskCreateResponse(BaseModel):
    message: str
    task_id: int

class TaskResponse(BaseModel):
    id: int
    nombre: str
    tipo_labor_id: int
    fecha_inicio_estimada: date
    fecha_finalizacion: Optional[date]
    descripcion: Optional[str]
    estado_id: int
    lote_id: int

    class Config:
        from_attributes = True

class PaginatedTaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total_tasks: int
    page: int
    per_page: int
    total_pages: int

class AssignmentCreate(BaseModel):
    usuario_ids: List[int]
    tarea_labor_cultural_id: int
    
class AssignmentCreateSingle(BaseModel):
    usuario_id: int
    tarea_labor_cultural_id: int

class TaskStateResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    
class TaskStateListResponse(BaseModel):
    states: List[TaskStateResponse]
