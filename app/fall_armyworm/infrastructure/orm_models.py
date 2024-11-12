from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, Text, Numeric, Enum
from sqlalchemy.sql import func
import enum
from app.infrastructure.db.connection import Base

# Movemos los Enums aquí
class DetectionResultEnum(enum.Enum):
    leaf_with_larva = "leaf_with_larva"
    healthy_leaf = "healthy_leaf"
    damaged_leaf = "damaged_leaf"

class EstadoMonitoreoEnum(enum.Enum):
    processing = "processing"
    completed = "completed"
    failed = "failed"
    partial = "partial"

class MonitoreoFitosanitario(Base):
    """Modelo para monitoreo fitosanitario"""
    __tablename__ = "monitoreo_fitosanitario"

    id = Column(Integer, primary_key=True)
    tarea_labor_id = Column(Integer, ForeignKey("tarea_labor_cultural.id"), nullable=False)
    fecha_monitoreo = Column(TIMESTAMP(timezone=True), nullable=False)
    observaciones = Column(Text)
    estado = Column(
        Enum(
            EstadoMonitoreoEnum,
            name='estado_monitoreo_enum'
        ),
        nullable=False,
        default=EstadoMonitoreoEnum.processing
    )
    cantidad_imagenes = Column(Integer, nullable=False, default=0)

class FallArmywormDetection(Base):
    """Modelo para detecciones individuales de gusano cogollero"""
    __tablename__ = "deteccion_gusano_cogollero"

    id = Column(Integer, primary_key=True)
    monitoreo_fitosanitario_id = Column(Integer, ForeignKey("monitoreo_fitosanitario.id"), nullable=False)
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