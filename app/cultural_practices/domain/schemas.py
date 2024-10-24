from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import date, timedelta
from typing import List, Optional

from app.infrastructure.utils.validators import validate_no_emojis
        
class TaskCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=255)
    tipo_labor_id: int
    fecha_inicio_estimada: date
    descripcion: Optional[str] = Field(None, max_length=500)
    estado_id: int
    lote_id: int
    
    _validate_no_emojis = field_validator('nombre')(validate_no_emojis)
    
    @field_validator('fecha_inicio_estimada')
    def validar_fecha_inicio_estimada(cls, value):
        # Calcular la fecha límite (un mes atrás)
        fecha_limite = date.today() - timedelta(days=30)
        
        if value < fecha_limite:
            raise ValueError('La fecha de inicio estimada no puede ser anterior a un mes desde la fecha actual.')
        return value

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

    model_config = ConfigDict(from_attributes=True)

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

class TaskTypeResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    
class TaskTypeListResponse(BaseModel):
    task_types: List[TaskTypeResponse]
