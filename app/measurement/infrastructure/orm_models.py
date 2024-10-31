from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base

class UnitCategory(Base):
    """Modelo para la categoría de unidades de medida.

    Este modelo representa una categoría a la que pertenecen diferentes unidades de medida.

    Attributes:
        id (int): ID único de la categoría.
        nombre (str): Nombre de la categoría, debe ser único y no nulo.
        descripcion (str): Descripción de la categoría.
        unidades (List[UnitOfMeasure]): Relación con las unidades de medida asociadas a esta categoría.
    """
    __tablename__ = "categoria_unidad_medida"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)

    unidades = relationship("UnitOfMeasure", back_populates="categoria")

class UnitOfMeasure(Base):
    """Modelo para las unidades de medida.

    Este modelo representa una unidad de medida específica que pertenece a una categoría.

    Attributes:
        id (int): ID único de la unidad de medida.
        nombre (str): Nombre de la unidad de medida, debe ser único y no nulo.
        abreviatura (str): Abreviatura de la unidad de medida, debe ser única y no nula.
        categoria_id (int): ID de la categoría a la que pertenece esta unidad de medida.
        categoria (UnitCategory): Relación con la categoría de la unidad de medida.
    """
    __tablename__ = "unidad_medida"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    abreviatura = Column(String(10), unique=True, nullable=False)
    categoria_id = Column(Integer, ForeignKey('categoria_unidad_medida.id'), nullable=False)

    categoria = relationship("UnitCategory", back_populates="unidades")