from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class LogSeverity(str, Enum):
    """Enumeración para los niveles de severidad del log."""
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'

class ActivityLogCreate(BaseModel):
    """Esquema para crear un nuevo log de actividad."""
    usuario_id: Optional[int] = None
    tipo_accion_id: int
    tabla_afectada: str
    registro_id: Optional[int] = None
    valor_anterior: Optional[Dict[str, Any]] = None
    valor_nuevo: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    severidad: LogSeverity = LogSeverity.INFO
    descripcion: Optional[str] = None

class ActivityLogResponse(BaseModel):
    """Esquema para la respuesta de un log de actividad."""
    id: int
    usuario_id: int
    tipo_accion_id: int
    tabla_afectada: str
    registro_id: Optional[int] = None
    valor_anterior: Optional[Dict[str, Any]] = None
    valor_nuevo: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    severidad: LogSeverity
    descripcion: Optional[str] = None
    fecha_creacion: datetime
    
    model_config = ConfigDict(from_attributes=True)

class LogActionTypeCreate(BaseModel):
    """Esquema para crear un nuevo tipo de acción de log."""
    nombre: str
    descripcion: Optional[str] = None

class LogActionTypeResponse(BaseModel):
    """Esquema para la respuesta de un tipo de acción de log."""
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha_creacion: datetime
    fecha_modificacion: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True) 