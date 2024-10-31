from sqlalchemy import Column, Integer, ForeignKey, String, Text, Date
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base

class Assignment(Base):
    """Modelo de asignación de tareas.

    Este modelo representa la relación entre un usuario y una tarea de labor cultural.

    Attributes:
        usuario_id (int): ID del usuario asignado a la tarea.
        tarea_labor_cultural_id (int): ID de la tarea de labor cultural asignada.
        usuario (User): Relación con el modelo User.
        tarea (CulturalTask): Relación con el modelo CulturalTask.
    """
    __tablename__ = "asignacion"
    
    usuario_id = Column(Integer, ForeignKey("usuario.id"), primary_key=True, nullable=False)
    tarea_labor_cultural_id = Column(Integer, ForeignKey("tarea_labor_cultural.id"), primary_key=True, nullable=False)

    usuario = relationship("User", back_populates="asignaciones")
    tarea = relationship("CulturalTask", back_populates="asignaciones")
    
class CulturalTask(Base):
    """Modelo de tarea de labor cultural.

    Este modelo representa una tarea de labor cultural que puede ser asignada a un usuario.

    Attributes:
        id (int): ID único de la tarea.
        nombre (str): Nombre de la tarea.
        tipo_labor_id (int): ID del tipo de labor cultural.
        fecha_inicio_estimada (date): Fecha estimada de inicio de la tarea.
        fecha_finalizacion (date): Fecha de finalización de la tarea.
        descripcion (str): Descripción de la tarea.
        estado_id (int): ID del estado de la tarea.
        lote_id (int): ID del lote asociado a la tarea.
        tipo_labor (CulturalTaskType): Relación con el modelo CulturalTaskType.
        estado (CulturalTaskState): Relación con el modelo CulturalTaskState.
        asignaciones (List[Assignment]): Lista de asignaciones de la tarea.
        lote (Plot): Relación con el modelo Plot.
    """
    __tablename__ = "tarea_labor_cultural"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    tipo_labor_id = Column(Integer, ForeignKey("tipo_labor_cultural.id"), nullable=False)
    fecha_inicio_estimada = Column(Date, nullable=False)
    fecha_finalizacion = Column(Date, nullable=True)
    descripcion = Column(Text, nullable=True)
    estado_id = Column(Integer, ForeignKey("estado_tarea_labor_cultural.id"), nullable=False)
    lote_id = Column(Integer, ForeignKey('lote.id'), nullable=False)

    # Relaciones
    tipo_labor = relationship("CulturalTaskType", back_populates="tareas")
    estado = relationship("CulturalTaskState", back_populates="tareas")
    asignaciones = relationship("Assignment", back_populates="tarea")    
    lote = relationship("Plot", back_populates="tareas")


class CulturalTaskState(Base):
    """Modelo de estado de tarea de labor cultural.

    Este modelo representa los diferentes estados que puede tener una tarea de labor cultural.

    Attributes:
        id (int): ID único del estado.
        nombre (str): Nombre del estado.
        descripcion (str): Descripción del estado.
        tareas (List[CulturalTask]): Lista de tareas asociadas a este estado.
    """
    __tablename__ = "estado_tarea_labor_cultural"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)

    # Relación con CulturalTask
    tareas = relationship("CulturalTask", back_populates="estado")
    
class CulturalTaskType(Base):
    """Modelo de tipo de labor cultural.

    Este modelo representa los diferentes tipos de tareas de labor cultural.

    Attributes:
        id (int): ID único del tipo de labor.
        nombre (str): Nombre del tipo de labor.
        descripcion (str): Descripción del tipo de labor.
        tareas (List[CulturalTask]): Lista de tareas asociadas a este tipo de labor.
    """
    __tablename__ = "tipo_labor_cultural"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text)

    # Relación con CulturalTask
    tareas = relationship("CulturalTask", back_populates="tipo_labor")