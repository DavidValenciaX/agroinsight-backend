from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, Enum as SQLAlchemyEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from app.infrastructure.db.connection import Base
from app.user.infrastructure.orm_models import User

class LogSeverityEnum(str, Enum):
    """Enumeración para los niveles de severidad del log."""
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'

class LogActionType(Base):
    """Modelo para tipos de acciones de log."""
    __tablename__ = "tipo_accion_log"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    fecha_creacion = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp(), nullable=False)
    fecha_modificacion = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relación con ActivityLog
    logs = relationship("ActivityLog", back_populates="tipo_accion")

class ActivityLog(Base):
    """Modelo para logs de actividad."""
    __tablename__ = "log_actividad"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuario.id', ondelete="SET NULL"), nullable=True)
    tipo_accion_id = Column(Integer, ForeignKey('tipo_accion_log.id'), nullable=False)
    tabla_afectada = Column(String(100), nullable=False)
    registro_id = Column(Integer, nullable=True)
    valor_anterior = Column(JSON, nullable=True)
    valor_nuevo = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    severidad = Column(SQLAlchemyEnum(LogSeverityEnum), nullable=False, default=LogSeverityEnum.INFO)
    descripcion = Column(Text, nullable=True)

    # Relaciones
    usuario = relationship("User", back_populates="logs")
    tipo_accion = relationship("LogActionType", back_populates="logs")