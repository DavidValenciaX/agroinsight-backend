from sqlalchemy import Column, Integer, ForeignKey, String, Text, Date, DECIMAL
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base

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