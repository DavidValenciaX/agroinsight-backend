from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, Text, Numeric, Enum, Date
from sqlalchemy.sql import func
import enum
from app.infrastructure.db.connection import Base

class SoilAnalysisStatusEnum(enum.Enum):
    processing = "processing"
    completed = "completed"
    failed = "failed"
    partial = "partial"

class SoilAnalysis(Base):
    """Modelo para análisis de suelo"""
    __tablename__ = "analisis_suelo"

    id = Column(Integer, primary_key=True)
    tarea_labor_id = Column(Integer, ForeignKey("tarea_labor_cultural.id"), nullable=False)
    fecha_analisis = Column(Date, nullable=False)
    estado = Column(
        Enum(
            SoilAnalysisStatusEnum,
            name='soil_analysis_status_enum'
        ),
        nullable=False,
        default=SoilAnalysisStatusEnum.processing
    )
    cantidad_imagenes = Column(Integer, nullable=False, default=0)
    observaciones = Column(Text)

class SoilClassification(Base):
    """Modelo para clasificaciones individuales de tipo de suelo"""
    __tablename__ = "clasificacion_tipo_suelo"

    id = Column(Integer, primary_key=True)
    analisis_suelo_id = Column(Integer, ForeignKey("analisis_suelo.id"), nullable=False)
    imagen_url = Column(String(255), nullable=False)
    imagen_public_id = Column(String(255), nullable=False)
    resultado_analisis_id = Column(Integer, ForeignKey("tipo_suelo.id"), nullable=False)
    confianza_clasificacion = Column(Numeric(5,2), nullable=False)
    prob_alluvial_soil = Column(Numeric(5,4), nullable=False)
    prob_black_soil = Column(Numeric(5,4), nullable=False)
    prob_cinder_soil = Column(Numeric(5,4), nullable=False)
    prob_clay_soil = Column(Numeric(5,4), nullable=False)
    prob_laterite_soil = Column(Numeric(5,4), nullable=False)
    prob_peat_soil = Column(Numeric(5,4), nullable=False)
    prob_yellow_soil = Column(Numeric(5,4), nullable=False)
    
class SoilType(Base):
    """Modelo para tipos de suelo"""
    __tablename__ = "tipo_suelo"

    id = Column(Integer, primary_key=True, server_default=func.identity())
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    color_id = Column(Integer, nullable=False)
    textura_id = Column(Integer, nullable=False)
    munsell_id = Column(Integer)
    caracteristicas_generales = Column(Text)
    recomendaciones_manejo = Column(Text)