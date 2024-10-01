from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base
from sqlalchemy.orm import relationship

class Finca(Base):
    __tablename__ = "finca"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    ubicacion = Column(String(255))
    area_total = Column(DECIMAL(10, 2), nullable=False)
    unidad_area_id = Column(Integer, ForeignKey('unidad_medida.id'), nullable=False)
    latitud = Column(DECIMAL(10, 8), nullable=False)
    longitud = Column(DECIMAL(11, 8), nullable=False)

    unidad_area = relationship("UnidadMedida")
    usuarios = relationship("User", secondary="usuario_finca", back_populates="fincas")
    lotes = relationship("Plot", back_populates="finca")
    
class CategoriaUnidadMedida(Base):
    __tablename__ = "categoria_unidad_medida"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)

    unidades = relationship("UnidadMedida", back_populates="categoria")

class UnidadMedida(Base):
    __tablename__ = "unidad_medida"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    abreviatura = Column(String(10), unique=True, nullable=False)
    categoria_id = Column(Integer, ForeignKey('categoria_unidad_medida.id'), nullable=False)

    categoria = relationship("CategoriaUnidadMedida", back_populates="unidades")
    
class UsuarioFinca(Base):
    __tablename__ = "usuario_finca"

    usuario_id = Column(Integer, ForeignKey('usuario.id'), primary_key=True)
    finca_id = Column(Integer, ForeignKey('finca.id'), primary_key=True)