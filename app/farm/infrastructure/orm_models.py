from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base
from sqlalchemy.sql import func

class Finca(Base):
    __tablename__ = "finca"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    ubicacion = Column(String(255))
    area_total = Column(DECIMAL(10, 2), nullable=False)
    unidad_area_id = Column(Integer, ForeignKey('unidad_medida.id'), nullable=False)
    latitud = Column(DECIMAL(10, 8), nullable=False)
    longitud = Column(DECIMAL(11, 8), nullable=False)
    fecha_creacion = Column(TIMESTAMP, server_default=func.now())
    fecha_modificacion = Column(TIMESTAMP, onupdate=func.now())

    unidad_area = relationship("UnidadMedida")
    usuarios = relationship("User", secondary="usuario_finca")
    lotes = relationship("Lote", back_populates="finca")

class UsuarioFinca(Base):
    __tablename__ = "usuario_finca"

    usuario_id = Column(Integer, ForeignKey('usuario.id'), primary_key=True)
    finca_id = Column(Integer, ForeignKey('finca.id'), primary_key=True)
    fecha_asignacion = Column(TIMESTAMP, server_default=func.now())
    fecha_modificacion = Column(TIMESTAMP, onupdate=func.now())

class Lote(Base):
    __tablename__ = "lote"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    area = Column(DECIMAL(10, 2), nullable=False)
    unidad_area_id = Column(Integer, ForeignKey('unidad_medida.id'), nullable=False)
    latitud = Column(DECIMAL(10, 8), nullable=False)
    longitud = Column(DECIMAL(11, 8), nullable=False)
    finca_id = Column(Integer, ForeignKey('finca.id'), nullable=False)
    fecha_creacion = Column(TIMESTAMP, server_default=func.now())
    fecha_modificacion = Column(TIMESTAMP, onupdate=func.now())

    finca = relationship("Finca", back_populates="lotes")
    unidad_area = relationship("UnidadMedida")
    
class CategoriaUnidadMedida(Base):
    __tablename__ = "categoria_unidad_medida"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    fecha_creacion = Column(TIMESTAMP, server_default=func.now())
    fecha_modificacion = Column(TIMESTAMP, onupdate=func.now())

    unidades = relationship("UnidadMedida", back_populates="categoria")

class UnidadMedida(Base):
    __tablename__ = "unidad_medida"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    abreviatura = Column(String(10), unique=True, nullable=False)
    categoria_id = Column(Integer, ForeignKey('categoria_unidad_medida.id'), nullable=False)
    fecha_creacion = Column(TIMESTAMP, server_default=func.now())
    fecha_modificacion = Column(TIMESTAMP, onupdate=func.now())

    categoria = relationship("CategoriaUnidadMedida", back_populates="unidades")