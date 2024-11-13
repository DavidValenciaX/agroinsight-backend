from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from typing_extensions import Annotated
from dataclasses import dataclass

from app.fall_armyworm.infrastructure.orm_models import DetectionResultEnum, EstadoMonitoreoEnum

# Definir tipos personalizados para mayor legibilidad
Probability = Annotated[float, Field(ge=0, le=1)]

class DetectionProbabilities(BaseModel):
    leaf_with_larva: Probability
    healthy_leaf: Probability
    damaged_leaf: Probability

class DetectionResponse(BaseModel):
    filename: str
    status: str = Field(..., pattern="^(success|error)$")
    predicted_class: DetectionResultEnum
    confidence: Probability
    probabilities: DetectionProbabilities

class FallArmywormDetectionResult(BaseModel):
    monitoring_id: int
    message: str
    results: List[DetectionResponse]

class MonitoreoFitosanitarioCreate(BaseModel):
    tarea_labor_id: int = Field(gt=0)
    fecha_monitoreo: datetime
    observaciones: Optional[str] = Field(None, max_length=500)
    estado: EstadoMonitoreoEnum = Field(default=EstadoMonitoreoEnum.processing)
    cantidad_imagenes: int = Field(gt=0)

class FallArmywormDetectionCreate(BaseModel):
    monitoreo_fitosanitario_id: int = Field(gt=0)
    imagen_url: str = Field(..., min_length=1)
    imagen_public_id: str = Field(..., min_length=1)
    resultado_deteccion: DetectionResultEnum
    confianza_deteccion: Probability
    prob_leaf_with_larva: Probability
    prob_healthy_leaf: Probability
    prob_damaged_leaf: Probability

@dataclass
class FileContent:
    filename: str
    content: bytes
    content_type: str

class DetectionResult(BaseModel):
    id: int
    imagen_url: str
    resultado_deteccion: DetectionResultEnum
    confianza_deteccion: Probability
    prob_leaf_with_larva: Probability
    prob_healthy_leaf: Probability
    prob_damaged_leaf: Probability

class MonitoreoFitosanitarioResult(BaseModel):
    id: int
    tarea_labor_id: int
    fecha_monitoreo: datetime
    observaciones: Optional[str]
    estado: EstadoMonitoreoEnum
    cantidad_imagenes: int
    detecciones: List[DetectionResult]