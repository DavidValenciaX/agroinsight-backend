from sqlalchemy import Column, Integer, ForeignKey, String, Text, Date, Text, DECIMAL
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base

class Assignment(Base):
    __tablename__ = "asignacion"
    
    usuario_id = Column(Integer, ForeignKey("usuario.id"), primary_key=True, nullable=False)
    tarea_labor_cultural_id = Column(Integer, ForeignKey("tarea_labor_cultural.id"), primary_key=True, nullable=False)

    usuario = relationship("User", back_populates="asignaciones")
    tarea = relationship("CulturalTask", back_populates="asignaciones")
    
class CulturalTask(Base):
    __tablename__ = "tarea_labor_cultural"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    tipo_labor_id = Column(Integer, ForeignKey("tipo_labor_cultural.id"), nullable=False)
    fecha_inicio_estimada = Column(Date, nullable=False)
    fecha_finalizacion = Column(Date)
    descripcion = Column(Text)
    estado_id = Column(Integer, ForeignKey("estado_tarea_labor_cultural.id"), nullable=False)
    lote_id = Column(Integer, ForeignKey('lote.id'), nullable=False)

    # Relaciones
    tipo_labor = relationship("CulturalTaskType", back_populates="tareas")
    estado = relationship("CulturalTaskState", back_populates="tareas")
    asignaciones = relationship("Assignment", back_populates="tarea")    
    lote = relationship("Plot", back_populates="tareas")


class CulturalTaskState(Base):
    __tablename__ = "estado_tarea_labor_cultural"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)

    # Relación con CulturalTask
    tareas = relationship("CulturalTask", back_populates="estado")
    
class CulturalTaskType(Base):
    __tablename__ = "tipo_labor_cultural"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text)

    # Relación con CulturalTask
    tareas = relationship("CulturalTask", back_populates="tipo_labor")