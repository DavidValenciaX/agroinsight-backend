from sqlalchemy import Column, Integer, Date, DECIMAL, ForeignKey, TIMESTAMP, func, String, Text
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base

class Crop(Base):
    """
    Representa la tabla 'cultivo' en la base de datos.

    Attributes:
        id (int): Identificador único del cultivo.
        lote_id (int): ID del lote asociado.
        variedad_maiz_id (int): ID de la variedad de maíz.
        fecha_siembra (date): Fecha de siembra.
        densidad_siembra (int): Densidad de siembra.
        densidad_siembra_unidad_id (int): ID de la unidad de medida para la densidad.
        estado_id (int): ID del estado del cultivo.
        fecha_cosecha (date): Fecha de cosecha (opcional).
        produccion_total (int): Producción total (opcional).
        produccion_total_unidad_id (int): ID de la unidad de medida para la producción (opcional).
        precio_venta_unitario (decimal): Precio de venta unitario (opcional).
        cantidad_vendida (int): Cantidad vendida (opcional).
        cantidad_vendida_unidad_id (int): ID de la unidad de medida para la cantidad vendida (opcional).
        ingreso_total (decimal): Ingreso total (opcional).
        costo_produccion (decimal): Costo de producción (opcional).
        moneda_id (int): ID de la moneda (opcional).
        fecha_venta (date): Fecha de venta (opcional).
        fecha_creacion (timestamp): Fecha de creación del registro.
        fecha_modificacion (timestamp): Fecha de última modificación del registro.
    """
    __tablename__ = "cultivo"

    id = Column(Integer, primary_key=True, index=True)
    lote_id = Column(Integer, ForeignKey('lote.id'), nullable=False)
    variedad_maiz_id = Column(Integer, ForeignKey('variedad_maiz.id'), nullable=False)
    fecha_siembra = Column(Date, nullable=False)
    densidad_siembra = Column(Integer, nullable=False)
    densidad_siembra_unidad_id = Column(Integer, ForeignKey('unidad_medida.id'), nullable=False)
    estado_id = Column(Integer, ForeignKey('estado_cultivo.id'), nullable=False)
    fecha_cosecha = Column(Date)
    produccion_total = Column(Integer)
    produccion_total_unidad_id = Column(Integer, ForeignKey('unidad_medida.id'))
    precio_venta_unitario = Column(DECIMAL(10, 2))
    cantidad_vendida = Column(Integer)
    cantidad_vendida_unidad_id = Column(Integer, ForeignKey('unidad_medida.id'))
    ingreso_total = Column(DECIMAL(15, 2))
    costo_produccion = Column(DECIMAL(15, 2))
    moneda_id = Column(Integer, ForeignKey('moneda.id'))
    fecha_venta = Column(Date)
    fecha_creacion = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.timezone('UTC', func.current_timestamp()))
    fecha_modificacion = Column(TIMESTAMP(timezone=True))

    # Relaciones
    lote = relationship("Plot", back_populates="cultivos")
    variedad_maiz = relationship("CornVariety")
    densidad_siembra_unidad = relationship("UnitOfMeasure", foreign_keys=[densidad_siembra_unidad_id])
    estado = relationship("CropState")
    produccion_total_unidad = relationship("UnitOfMeasure", foreign_keys=[produccion_total_unidad_id])
    cantidad_vendida_unidad = relationship("UnitOfMeasure", foreign_keys=[cantidad_vendida_unidad_id])
    moneda = relationship("Currency")

class CropState(Base):
    """
    Representa la tabla 'estado_cultivo' en la base de datos.

    Attributes:
        id (int): Identificador único del estado.
        nombre (str): Nombre del estado.
        descripcion (str): Descripción del estado.
    """
    __tablename__ = "estado_cultivo"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)

class CornVariety(Base):
    """
    Representa la tabla 'variedad_maiz' en la base de datos.

    Attributes:
        id (int): Identificador único de la variedad.
        nombre (str): Nombre de la variedad.
        descripcion (str): Descripción de la variedad.
    """
    __tablename__ = "variedad_maiz"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text)

class Currency(Base):
    """
    Representa la tabla 'moneda' en la base de datos.

    Attributes:
        id (int): Identificador único de la moneda.
        nombre (str): Nombre de la moneda.
        codigo (str): Código de la moneda.
        simbolo (str): Símbolo de la moneda.
    """
    __tablename__ = "moneda"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    codigo = Column(String(3), unique=True, nullable=False)
    simbolo = Column(String(5), nullable=False)

