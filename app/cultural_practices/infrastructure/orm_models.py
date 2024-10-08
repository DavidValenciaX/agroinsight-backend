from sqlalchemy import Column, Integer, ForeignKey, String, Text, Date, Text, DECIMAL
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base

class Asignacion(Base):
    __tablename__ = "asignacion"
    
    usuario_id = Column(Integer, ForeignKey("usuario.id"), primary_key=True, nullable=False)
    tarea_labor_cultural_id = Column(Integer, ForeignKey("tarea_labor_cultural.id"), primary_key=True, nullable=False)
    notas = Column(Text)

    usuario = relationship("User", back_populates="asignaciones")
    tarea = relationship("TareaLaborCultural", back_populates="asignaciones")
    
class TareaLaborCultural(Base):
    __tablename__ = "tarea_labor_cultural"

    id = Column(Integer, primary_key=True, index=True)
    tipo_labor_id = Column(Integer, ForeignKey("tipo_labor_cultural.id"), nullable=False)
    fecha_programada = Column(Date, nullable=False)
    descripcion = Column(Text)
    costo_mano_obra = Column(DECIMAL(10, 2), nullable=False, default=0)
    estado_id = Column(Integer, ForeignKey("estado_tarea_labor_cultural.id"), nullable=False)
    lote_id = Column(Integer, ForeignKey('lote.id'), nullable=False)
    observaciones = Column(Text)
    fecha_completada = Column(Date)

    # Relaciones
    tipo_labor = relationship("TipoLaborCultural", back_populates="tareas")
    estado = relationship("EstadoTareaLaborCultural", back_populates="tareas")
    asignaciones = relationship("Asignacion", back_populates="tarea")    
    lote = relationship("Plot", back_populates="tareas")

class EstadoTareaLaborCultural(Base):
    __tablename__ = "estado_tarea_labor_cultural"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)

    # Relación con TareaLaborCultural
    tareas = relationship("TareaLaborCultural", back_populates="estado")
    
class TipoLaborCultural(Base):
    __tablename__ = "tipo_labor_cultural"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text)

    # Relación con TareaLaborCultural
    tareas = relationship("TareaLaborCultural", back_populates="tipo_labor")