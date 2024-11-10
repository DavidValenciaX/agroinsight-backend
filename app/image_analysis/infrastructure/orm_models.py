from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, Text, Numeric, Enum
from sqlalchemy.sql import func
import enum
from app.infrastructure.db.connection import Base

class DetectionResultEnum(enum.Enum):
    """Enum para los posibles resultados de detección"""
    leaf_with_larva = "leaf_with_larva"
    healthy_leaf = "healthy_leaf"
    damaged_leaf = "damaged_leaf"

class FallArmywormDetectionGroup(Base):
    """Modelo para grupo de detecciones de gusano cogollero"""
    __tablename__ = "grupo_deteccion_gusano_cogollero"

    id = Column(Integer, primary_key=True)
    lote_id = Column(Integer, ForeignKey("lote.id"), nullable=False)
    fecha_deteccion = Column(TIMESTAMP(timezone=True), nullable=False)
    observaciones = Column(Text)

class FallArmywormDetection(Base):
    """Modelo para detecciones individuales de gusano cogollero"""
    __tablename__ = "deteccion_gusano_cogollero"

    id = Column(Integer, primary_key=True)
    grupo_deteccion_id = Column(Integer, ForeignKey("grupo_deteccion_gusano_cogollero.id"), nullable=False)
    imagen_url = Column(String(255), nullable=False)
    imagen_public_id = Column(String(255), nullable=False)
    resultado_deteccion = Column(
        Enum(
            DetectionResultEnum,
            name='deteccion_gusano_cogollero_resultado_deteccion_enum'
        ),
        nullable=False
    )
    confianza_deteccion = Column(Numeric(5,2), nullable=False)
    prob_leaf_with_larva = Column(Numeric(5,4), nullable=False)
    prob_healthy_leaf = Column(Numeric(5,4), nullable=False)
    prob_damaged_leaf = Column(Numeric(5,4), nullable=False)
    observaciones = Column(Text)