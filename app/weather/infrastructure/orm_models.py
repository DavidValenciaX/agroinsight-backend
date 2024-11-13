from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, Date, Time
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base

class WeatherLog(Base):
    """Modelo para registrar datos meteorológicos."""
    __tablename__ = "registro_meteorologico"

    id = Column(Integer, primary_key=True)
    lote_id = Column(Integer, ForeignKey('lote.id'), nullable=False)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    temperatura = Column(Float(precision=4), nullable=False)
    temperatura_sensacion = Column(Float(precision=4), nullable=False)
    temperatura_unidad_id = Column(Integer, ForeignKey('unidad_medida.id'))
    presion_atmosferica = Column(Float(precision=6), nullable=False)
    presion_unidad_id = Column(Integer, ForeignKey('unidad_medida.id'))
    humedad_relativa = Column(Float(precision=5), nullable=False)
    humedad_unidad_id = Column(Integer, ForeignKey('unidad_medida.id'))
    precipitacion = Column(Float(precision=6))
    precipitacion_unidad_id = Column(Integer, ForeignKey('unidad_medida.id'))
    indice_uv = Column(Float(precision=3), nullable=False)
    nubosidad = Column(Float(precision=5), nullable=False)
    nubosidad_unidad_id = Column(Integer, ForeignKey('unidad_medida.id'))
    velocidad_viento = Column(Float(precision=5), nullable=False)
    velocidad_viento_unidad_id = Column(Integer, ForeignKey('unidad_medida.id'))
    direccion_viento = Column(Integer, nullable=False)
    direccion_viento_unidad_id = Column(Integer, ForeignKey('unidad_medida.id'))
    rafaga_viento = Column(Float(precision=5))
    rafaga_viento_unidad_id = Column(Integer, ForeignKey('unidad_medida.id'))
    visibilidad = Column(Integer)
    visibilidad_unidad_id = Column(Integer, ForeignKey('unidad_medida.id'))
    punto_rocio = Column(Float(precision=4))
    punto_rocio_unidad_id = Column(Integer, ForeignKey('unidad_medida.id'))
    descripcion_clima = Column(String(100))
    codigo_clima = Column(String(10))

    # Relaciones
    lote = relationship("Plot", back_populates="registros_meteorologicos")
    temperatura_unidad = relationship("UnitOfMeasure", foreign_keys=[temperatura_unidad_id])
    presion_unidad = relationship("UnitOfMeasure", foreign_keys=[presion_unidad_id])
    humedad_unidad = relationship("UnitOfMeasure", foreign_keys=[humedad_unidad_id])
    precipitacion_unidad = relationship("UnitOfMeasure", foreign_keys=[precipitacion_unidad_id])
    nubosidad_unidad = relationship("UnitOfMeasure", foreign_keys=[nubosidad_unidad_id])
    velocidad_viento_unidad = relationship("UnitOfMeasure", foreign_keys=[velocidad_viento_unidad_id])
    direccion_viento_unidad = relationship("UnitOfMeasure", foreign_keys=[direccion_viento_unidad_id])
    rafaga_viento_unidad = relationship("UnitOfMeasure", foreign_keys=[rafaga_viento_unidad_id])
    visibilidad_unidad = relationship("UnitOfMeasure", foreign_keys=[visibilidad_unidad_id])
    punto_rocio_unidad = relationship("UnitOfMeasure", foreign_keys=[punto_rocio_unidad_id]) 