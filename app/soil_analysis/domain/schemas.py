from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from typing_extensions import Annotated
from dataclasses import dataclass

from app.soil_analysis.infrastructure.orm_models import SoilAnalysisStatusEnum

# Definir tipos personalizados para mayor legibilidad
Probability = Annotated[float, Field(ge=0, le=1)]

class SoilProbabilities(BaseModel):
    """Soil probabilities with field aliases to match API response"""
    alluvial_soil: Probability = Field(..., alias="Alluvial Soil")
    black_soil: Probability = Field(..., alias="Black Soil")
    cinder_soil: Probability = Field(..., alias="Cinder Soil")
    clay_soil: Probability = Field(..., alias="Clay Soil")
    laterite_soil: Probability = Field(..., alias="Laterite Soil")
    peat_soil: Probability = Field(..., alias="Peat Soil")
    yellow_soil: Probability = Field(..., alias="Yellow Soil")

    class Config:
        populate_by_name = True
        populate_by_name = True

class SoilClassificationResponse(BaseModel):
    filename: str
    status: str = Field(..., pattern="^(success|error)$")
    predicted_class: str
    confidence: Probability
    probabilities: SoilProbabilities

    class Config:
        populate_by_name = True
        
class PredictionServiceResponse(BaseModel):
    message: str
    results: List[SoilClassificationResponse]

class SoilAnalysisResponse(BaseModel):
    analysis_id: int
    message: str
    results: List[SoilClassificationResponse]

    class Config:
        populate_by_name = True

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
    
class ClassificationResult(BaseModel):
    id: int
    imagen_url: str
    resultado_analisis: str
    confianza_clasificacion: Probability
    prob_alluvial_soil: Probability
    prob_black_soil: Probability
    prob_cinder_soil: Probability
    prob_clay_soil: Probability
    prob_laterite_soil: Probability
    prob_peat_soil: Probability
    prob_yellow_soil: Probability

class SoilAnalysisResult(BaseModel):
    id: int
    tarea_labor_id: int
    fecha_analisis: datetime
    observaciones: Optional[str]
    estado: SoilAnalysisStatusEnum
    cantidad_imagenes: int
    clasificaciones: List[ClassificationResult]