from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List
from datetime import datetime
from typing_extensions import Annotated
from dataclasses import dataclass

# Definir tipos personalizados para mayor legibilidad
Probability = Annotated[float, Field(ge=0, le=1)]

class DetectionResult(str, Enum):
    LEAF_WITH_LARVA = "leaf_with_larva"
    HEALTHY_LEAF = "healthy_leaf"
    DAMAGED_LEAF = "damaged_leaf"

class DetectionProbabilities(BaseModel):
    leaf_with_larva: Probability
    healthy_leaf: Probability
    damaged_leaf: Probability

class DetectionResponse(BaseModel):
    status: str = Field(..., pattern="^(success|error)$")
    predicted_class: DetectionResult
    confidence: Probability
    probabilities: DetectionProbabilities

class FallArmywormDetectionResult(BaseModel):
    results: List[DetectionResponse]

class MonitoreoFitosanitarioCreate(BaseModel):
    tarea_labor_id: int = Field(gt=0)
    fecha_monitoreo: datetime
    observaciones: Optional[str] = Field(None, max_length=500)

class FallArmywormDetectionCreate(BaseModel):
    monitoreo_fitosanitario_id: int = Field(gt=0)
    imagen_url: str = Field(..., min_length=1)
    imagen_public_id: str = Field(..., min_length=1)
    resultado_deteccion: DetectionResult
    confianza_deteccion: Probability
    prob_leaf_with_larva: Probability
    prob_healthy_leaf: Probability
    prob_damaged_leaf: Probability
    observaciones: Optional[str] = Field(None, max_length=500)

@dataclass
class FileContent:
    filename: str
    content: bytes
    content_type: str