from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List
from datetime import datetime

class DetectionResult(str, Enum):
    LEAF_WITH_LARVA = "leaf_with_larva"
    HEALTHY_LEAF = "healthy_leaf"
    DAMAGED_LEAF = "damaged_leaf"

class DetectionProbabilities(BaseModel):
    leaf_with_larva: float
    healthy_leaf: float
    damaged_leaf: float

class DetectionResponse(BaseModel):
    status: str
    predicted_class: DetectionResult
    confidence: float
    probabilities: DetectionProbabilities

class FallArmywormDetectionResult(BaseModel):
    results: List[DetectionResponse]

class MonitoreoFitosanitarioCreate(BaseModel):
    tarea_labor_id: int
    fecha_monitoreo: datetime
    observaciones: Optional[str] = None

class FallArmywormDetectionCreate(BaseModel):
    monitoreo_fitosanitario_id: int
    imagen_url: str
    imagen_public_id: str
    resultado_deteccion: DetectionResult
    confianza_deteccion: float
    prob_leaf_with_larva: float
    prob_healthy_leaf: float
    prob_damaged_leaf: float
    observaciones: Optional[str] = None