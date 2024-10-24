from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base

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