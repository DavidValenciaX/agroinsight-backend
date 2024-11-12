from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from typing_extensions import Annotated
from dataclasses import dataclass

from app.soil_analysis.infrastructure.orm_models import SoilAnalysisStatusEnum

# Definir tipos personalizados para mayor legibilidad
Probability = Annotated[float, Field(ge=0, le=1)]

class SoilProbabilities(BaseModel):
    alluvial_soil: Probability
    black_soil: Probability
    cinder_soil: Probability
    clay_soil: Probability
    laterite_soil: Probability
    peat_soil: Probability
    yellow_soil: Probability

class SoilClassificationResponse(BaseModel):
    status: str = Field(..., pattern="^(success|error)$")
    predicted_class: str
    confidence: Probability
    probabilities: SoilProbabilities

class SoilAnalysisResult(BaseModel):
    results: List[SoilClassificationResponse]

class SoilAnalysisCreate(BaseModel):
    tarea_labor_id: int = Field(gt=0)
    fecha_analisis: date
    observaciones: Optional[str] = Field(None, max_length=500)
    estado: SoilAnalysisStatusEnum = Field(default=SoilAnalysisStatusEnum.processing)
    cantidad_imagenes: int = Field(gt=0)

class SoilClassificationCreate(BaseModel):
    analisis_suelo_id: int = Field(gt=0)
    imagen_url: str = Field(..., min_length=1)
    imagen_public_id: str = Field(..., min_length=1)
    resultado_analisis_id: int = Field(gt=0)
    confianza_clasificacion: Probability
    prob_alluvial_soil: Probability
    prob_black_soil: Probability
    prob_cinder_soil: Probability
    prob_clay_soil: Probability
    prob_laterite_soil: Probability
    prob_peat_soil: Probability
    prob_yellow_soil: Probability

@dataclass
class FileContent:
    filename: str
    content: bytes
    content_type: str