from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base

class Farm(Base):
    """Modelo ORM que representa una finca o granja en el sistema.

    Esta clase define la estructura y relaciones de la tabla 'finca' en la base de datos.

    Attributes:
        id (int): Identificador único de la finca.
        nombre (str): Nombre de la finca. Máximo 100 caracteres.
        ubicacion (str): Ubicación o dirección de la finca. Máximo 255 caracteres.
        area_total (Decimal): Área total de la finca con precisión de 2 decimales.
        unidad_area_id (int): Clave foránea que referencia la unidad de medida del área.
        unidad_area (UnitOfMeasure): Relación con la unidad de medida del área.
        lotes (List[Plot]): Relación con los lotes o parcelas de la finca.
        usuario_roles (List[UserFarmRole]): Relación con los roles de usuarios en la finca.
    """

    __tablename__ = "finca"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    ubicacion = Column(String(255))
    area_total = Column(DECIMAL(10, 2), nullable=False)
    unidad_area_id = Column(Integer, ForeignKey('unidad_medida.id'), nullable=False)

    unidad_area = relationship("UnitOfMeasure")
    lotes = relationship("Plot", back_populates="finca")
    usuario_roles = relationship("UserFarmRole", back_populates="finca")