from sqlalchemy import Column, Integer, ForeignKey, String, Text, Date, DECIMAL, TIMESTAMP
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base
from datetime import datetime

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
        costo_mano_obra (List[LaborCost]): Lista de costos de mano de obra asociados a la tarea.
        insumos (List[TaskInput]): Lista de insumos asociados a la tarea.
        maquinarias (List[TaskMachinery]): Lista de maquinarias asociadas a la tarea.
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
    costo_mano_obra = relationship("LaborCost", back_populates="tarea")
    insumos = relationship("TaskInput", back_populates="tarea")
    maquinarias = relationship("TaskMachinery", back_populates="tarea")


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

class LaborCost(Base):
    """Modelo de costo de mano de obra para una tarea cultural."""
    __tablename__ = "costo_mano_obra"

    id = Column(Integer, primary_key=True, index=True)
    tarea_labor_id = Column(Integer, ForeignKey("tarea_labor_cultural.id"), unique=True, nullable=False)
    cantidad_trabajadores = Column(Integer, nullable=False)
    horas_trabajadas = Column(DECIMAL(5,2), nullable=False)
    costo_hora = Column(DECIMAL(10,2), nullable=False)
    costo_total = Column(DECIMAL(10,2), nullable=False)
    observaciones = Column(Text)

    # Relación con CulturalTask
    tarea = relationship("CulturalTask", back_populates="costo_mano_obra")

class AgriculturalInputCategory(Base):
    """Modelo de categoría de insumos agrícolas."""
    __tablename__ = "categoria_insumo_agricola"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text)

    # Relación con AgriculturalInput
    insumos = relationship("AgriculturalInput", back_populates="categoria")

class AgriculturalInput(Base):
    """Modelo de insumo agrícola."""
    __tablename__ = "insumo_agricola"

    id = Column(Integer, primary_key=True, index=True)
    categoria_id = Column(Integer, ForeignKey("categoria_insumo_agricola.id"), nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    unidad_medida_id = Column(Integer, ForeignKey("unidad_medida.id"), nullable=False)
    costo_unitario = Column(DECIMAL(10,2), nullable=False)
    stock_actual = Column(DECIMAL(10,2), nullable=False, default=0)

    # Relaciones
    categoria = relationship("AgriculturalInputCategory", back_populates="insumos")
    unidad_medida = relationship("UnitOfMeasure")
    usos_tarea = relationship("TaskInput", back_populates="insumo")

class TaskInput(Base):
    """Modelo de uso de insumo en una tarea."""
    __tablename__ = "tarea_insumo"

    id = Column(Integer, primary_key=True, index=True)
    tarea_labor_id = Column(Integer, ForeignKey("tarea_labor_cultural.id"), nullable=False)
    insumo_id = Column(Integer, ForeignKey("insumo_agricola.id"), nullable=False)
    cantidad_utilizada = Column(DECIMAL(10,2), nullable=False)
    costo_total = Column(DECIMAL(10,2), nullable=False)
    fecha_aplicacion = Column(Date, nullable=True)
    observaciones = Column(Text)

    # Relaciones
    tarea = relationship("CulturalTask", back_populates="insumos")
    insumo = relationship("AgriculturalInput", back_populates="usos_tarea")

class MachineryType(Base):
    """Modelo de tipo de maquinaria agrícola."""
    __tablename__ = "tipo_maquinaria_agricola"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(String(255), nullable=False)

    # Relación con AgriculturalMachinery
    maquinarias = relationship("AgriculturalMachinery", back_populates="tipo_maquinaria")

class AgriculturalMachinery(Base):
    """Modelo de maquinaria agrícola."""
    __tablename__ = "maquinaria_agricola"

    id = Column(Integer, primary_key=True, index=True)
    tipo_maquinaria_id = Column(Integer, ForeignKey("tipo_maquinaria_agricola.id"), nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    modelo = Column(String(100))
    numero_serie = Column(String(100))
    costo_hora = Column(DECIMAL(10,2), nullable=False)

    # Relaciones
    tipo_maquinaria = relationship("MachineryType", back_populates="maquinarias")
    usos_tarea = relationship("TaskMachinery", back_populates="maquinaria")

class TaskMachinery(Base):
    """Modelo de uso de maquinaria en una tarea."""
    __tablename__ = "tarea_maquinaria"

    id = Column(Integer, primary_key=True, index=True)
    tarea_labor_id = Column(Integer, ForeignKey("tarea_labor_cultural.id"), nullable=False)
    maquinaria_id = Column(Integer, ForeignKey("maquinaria_agricola.id"), nullable=False)
    fecha_uso = Column(Date, nullable=True)
    horas_uso = Column(DECIMAL(5,2), nullable=False)
    costo_total = Column(DECIMAL(10,2), nullable=False)
    observaciones = Column(Text)

    # Relaciones
    tarea = relationship("CulturalTask", back_populates="maquinarias")
    maquinaria = relationship("AgriculturalMachinery", back_populates="usos_tarea")