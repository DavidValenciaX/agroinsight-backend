from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base

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