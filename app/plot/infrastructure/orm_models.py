from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base

class Plot(Base):
    """Modelo ORM que representa un lote en el sistema.

    Esta clase define la estructura y relaciones de la tabla 'lote' en la base de datos.

    Attributes:
        id (int): Identificador único del lote.
        nombre (str): Nombre del lote. Debe tener un máximo de 100 caracteres.
        area (Decimal): Área del lote. Debe ser un valor positivo con precisión de 2 decimales.
        unidad_area_id (int): Clave foránea que referencia la unidad de medida del área.
        latitud (Decimal): Latitud del lote con precisión de 8 decimales.
        longitud (Decimal): Longitud del lote con precisión de 8 decimales.
        finca_id (int): Clave foránea que referencia la finca a la que pertenece el lote.
        unidad_area (UnitOfMeasure): Relación con la unidad de medida del área.
        finca (Farm): Relación con la finca a la que pertenece el lote.
        tareas (List[CulturalTask]): Relación con las tareas culturales asociadas al lote.
        cultivos (List[Crop]): Relación con los cultivos asociados al lote.
        costos_mantenimiento (Decimal): Costos de mantenimiento del lote. Debe ser un valor positivo con precisión de 2 decimales.
    """

    __tablename__ = "lote"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    area = Column(DECIMAL(10, 2), nullable=False)
    unidad_area_id = Column(Integer, ForeignKey('unidad_medida.id'), nullable=False)
    latitud = Column(DECIMAL(10, 8), nullable=False)
    longitud = Column(DECIMAL(11, 8), nullable=False)
    finca_id = Column(Integer, ForeignKey('finca.id'), nullable=False)
    costos_mantenimiento = Column(DECIMAL(15, 2), nullable=False, default=0.00)

    unidad_area = relationship("UnitOfMeasure")
    finca = relationship("Farm", back_populates="lotes")
    registros_meteorologicos = relationship("WeatherLog", back_populates="lote")
    tareas = relationship("CulturalTask", back_populates="lote")
    cultivos = relationship("Crop", back_populates="lote")