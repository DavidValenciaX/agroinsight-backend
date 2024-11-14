from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import date, timedelta
from typing import List, Optional
from decimal import Decimal

from app.infrastructure.utils.validators import validate_no_emojis, validate_no_special_chars, validate_no_xss
        
class TaskCreate(BaseModel):
    """Modelo para la creación de una tarea de labor cultural.

    Attributes:
        nombre (str): Nombre de la tarea. Debe tener entre 3 y 255 caracteres.
        tipo_labor_id (int): ID del tipo de labor cultural.
        fecha_inicio_estimada (date): Fecha estimada de inicio de la tarea.
        descripcion (Optional[str]): Descripción de la tarea, máximo 500 caracteres.
        estado_id (int): ID del estado de la tarea.
        lote_id (int): ID del lote asociado a la tarea.
    """
    nombre: str = Field(..., min_length=3, max_length=255)
    tipo_labor_id: int
    fecha_inicio_estimada: date
    descripcion: Optional[str] = Field(None, max_length=500)
    estado_id: int = Field(default=1)
    lote_id: int
    
    @field_validator('nombre')
    def validate_no_emojis_nombre(cls, value):
        """Valida que el nombre no contenga emojis."""
        return validate_no_emojis(value)
    
    @field_validator('nombre')
    def validate_no_special_chars_nombre(cls, value):
        """Valida que el nombre no contenga caracteres especiales."""
        return validate_no_special_chars(value)
    
    @field_validator('nombre')
    def validate_no_xss_nombre(cls, value):
        """Valida que el nombre no contenga XSS."""
        return validate_no_xss(value)
    
    @field_validator('fecha_inicio_estimada')
    def validar_fecha_inicio_estimada(cls, value):
        """Valida que la fecha de inicio estimada no sea anterior a un mes desde la fecha actual."""
        # Calcular la fecha límite (un mes atrás)
        fecha_limite = date.today() - timedelta(days=30)
        
        if value < fecha_limite:
            raise ValueError('La fecha de inicio estimada no puede ser anterior a un mes desde la fecha actual.')
        return value

class SuccessTaskCreateResponse(BaseModel):
    """Modelo de respuesta para la creación exitosa de una tarea.

    Attributes:
        message (str): Mensaje de éxito.
        task_id (int): ID de la tarea creada.
    """
    message: str
    task_id: int

class TaskResponse(BaseModel):
    """Modelo de respuesta para una tarea de labor cultural.

    Attributes:
        id (int): ID único de la tarea.
        nombre (str): Nombre de la tarea.
        tipo_labor_id (int): ID del tipo de labor cultural.
        tipo_labor_nombre (str): Nombre del tipo de labor cultural.
        fecha_inicio_estimada (date): Fecha estimada de inicio de la tarea.
        fecha_finalizacion (Optional[date]): Fecha de finalización de la tarea.
        descripcion (Optional[str]): Descripción de la tarea.
        estado_id (int): ID del estado de la tarea.
        estado_nombre (str): Nombre del estado de la tarea.
        lote_id (int): ID del lote asociado a la tarea.
    """
    id: int
    nombre: str
    tipo_labor_id: int
    tipo_labor_nombre: str
    fecha_inicio_estimada: date
    fecha_finalizacion: Optional[date]
    descripcion: Optional[str]
    estado_id: int
    estado_nombre: str
    lote_id: int

    model_config = ConfigDict(from_attributes=True)

class PaginatedTaskListResponse(BaseModel):
    """Modelo de respuesta paginada para la lista de tareas.

    Attributes:
        tasks (List[TaskResponse]): Lista de tareas.
        total_tasks (int): Total de tareas.
        page (int): Número de página actual.
        per_page (int): Cantidad de tareas por página.
        total_pages (int): Total de páginas.
    """
    tasks: List[TaskResponse]
    total_tasks: int
    page: int
    per_page: int
    total_pages: int

class AssignmentCreate(BaseModel):
    """Modelo para la creación de asignaciones de tareas.

    Attributes:
        usuario_ids (List[int]): Lista de IDs de usuarios a los que se asignará la tarea.
        tarea_labor_cultural_id (int): ID de la tarea de labor cultural.
    """
    usuario_ids: List[int]
    tarea_labor_cultural_id: int
    
class AssignmentCreateSingle(BaseModel):
    """Modelo para la creación de una asignación de tarea para un solo usuario.

    Attributes:
        usuario_id (int): ID del usuario al que se asignará la tarea.
        tarea_labor_cultural_id (int): ID de la tarea de labor cultural.
    """
    usuario_id: int
    tarea_labor_cultural_id: int

class TaskStateResponse(BaseModel):
    """Modelo de respuesta para el estado de una tarea.

    Attributes:
        id (int): ID único del estado.
        nombre (str): Nombre del estado.
        descripcion (Optional[str]): Descripción del estado.
    """
    id: int
    nombre: str
    descripcion: Optional[str] = None
    
class TaskStateListResponse(BaseModel):
    """Modelo de respuesta para la lista de estados de tareas.

    Attributes:
        states (List[TaskStateResponse]): Lista de estados de tareas.
    """
    states: List[TaskStateResponse]

class TaskTypeResponse(BaseModel):
    """Modelo de respuesta para el tipo de tarea.

    Attributes:
        id (int): ID único del tipo de labor.
        nombre (str): Nombre del tipo de labor.
        descripcion (Optional[str]): Descripción del tipo de labor.
    """
    id: int
    nombre: str
    descripcion: Optional[str] = None
    
class TaskTypeListResponse(BaseModel):
    """Modelo de respuesta para la lista de tipos de tareas.

    Attributes:
        task_types (List[TaskTypeResponse]): Lista de tipos de tareas.
    """
    task_types: List[TaskTypeResponse]

class LaborCostCreate(BaseModel):
    """Modelo para la creación de costos de mano de obra.

    Attributes:
        cantidad_trabajadores (int): Número de trabajadores.
        horas_trabajadas (Decimal): Horas trabajadas.
        costo_hora (Decimal): Costo por hora.
        observaciones (Optional[str]): Observaciones adicionales.
    """
    cantidad_trabajadores: int = Field(..., gt=0)
    horas_trabajadas: Decimal = Field(..., gt=0)
    costo_hora: Decimal = Field(..., gt=0)
    observaciones: Optional[str] = None

class TaskInputCreate(BaseModel):
    """Modelo para la creación de costos de insumos.

    Attributes:
        insumo_id (int): ID del insumo utilizado.
        cantidad_utilizada (Decimal): Cantidad utilizada del insumo.
        fecha_aplicacion (date): Fecha de aplicación del insumo.
        observaciones (Optional[str]): Observaciones adicionales.
    """
    insumo_id: int
    cantidad_utilizada: Decimal = Field(..., gt=0)
    fecha_aplicacion: Optional[date] = None
    observaciones: Optional[str] = None

class TaskMachineryCreate(BaseModel):
    """Modelo para la creación de costos de maquinaria.

    Attributes:
        maquinaria_id (int): ID de la maquinaria utilizada.
        fecha_uso (date): Fecha de uso de la maquinaria.
        horas_uso (Decimal): Horas de uso de la maquinaria.
        observaciones (Optional[str]): Observaciones adicionales.
    """
    maquinaria_id: int
    fecha_uso: Optional[date] = None
    horas_uso: Decimal = Field(..., gt=0)
    observaciones: Optional[str] = None

class TaskCostsCreate(BaseModel):
    """Modelo para la creación de todos los costos asociados a una tarea.

    Attributes:
        labor_cost (Optional[LaborCostCreate]): Costos de mano de obra.
        inputs (Optional[List[TaskInputCreate]]): Lista de insumos utilizados.
        machinery (Optional[List[TaskMachineryCreate]]): Lista de maquinaria utilizada.
    """
    labor_cost: Optional[LaborCostCreate] = None
    inputs: Optional[List[TaskInputCreate]] = None
    machinery: Optional[List[TaskMachineryCreate]] = None

class CostRegistrationResponse(BaseModel):
    """Modelo de respuesta para el registro de costos.

    Attributes:
        message: str: Mensaje de éxito.
        labor_cost_registered: bool: Indica si se registraron costos de mano de obra.
        inputs_registered: int: Cantidad de insumos registrados.
        machinery_registered: int: Cantidad de maquinaria registrada.
    """
    message: str
    labor_cost_registered: bool
    inputs_registered: int
    machinery_registered: int
