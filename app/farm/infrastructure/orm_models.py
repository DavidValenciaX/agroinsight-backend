from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base
from sqlalchemy.orm import relationship

class Farm(Base):
    __tablename__ = "finca"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    ubicacion = Column(String(255))
    area_total = Column(DECIMAL(10, 2), nullable=False)
    unidad_area_id = Column(Integer, ForeignKey('unidad_medida.id'), nullable=False)

    unidad_area = relationship("UnitOfMeasure")
    lotes = relationship("Plot", back_populates="finca")
    usuario_roles = relationship("UserFarmRole", back_populates="finca")
    
class UnitCategory(Base):
    __tablename__ = "categoria_unidad_medida"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)

    unidades = relationship("UnitOfMeasure", back_populates="categoria")

class UnitOfMeasure(Base):
    __tablename__ = "unidad_medida"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    abreviatura = Column(String(10), unique=True, nullable=False)
    categoria_id = Column(Integer, ForeignKey('categoria_unidad_medida.id'), nullable=False)

    categoria = relationship("UnitCategory", back_populates="unidades")