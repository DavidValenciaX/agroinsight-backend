from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base

class Plot(Base):
    __tablename__ = "lote"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    area = Column(DECIMAL(10, 2), nullable=False)
    unidad_area_id = Column(Integer, ForeignKey('unidad_medida.id'), nullable=False)
    latitud = Column(DECIMAL(10, 8), nullable=False)
    longitud = Column(DECIMAL(11, 8), nullable=False)
    finca_id = Column(Integer, ForeignKey('finca.id'), nullable=False)

    unidad_area = relationship("UnidadMedida")
    finca = relationship("Finca", back_populates="lotes")
    asignaciones = relationship("Asignacion", back_populates="lote")