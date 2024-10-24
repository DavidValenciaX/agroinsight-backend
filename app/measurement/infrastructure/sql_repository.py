
from typing import Optional
from sqlalchemy.orm import Session
from app.measurement.infrastructure.orm_models import UnitOfMeasure, UnitCategory

class MeasurementRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_unit_of_measure_by_id(self, unit_id: int) -> Optional[UnitOfMeasure]:
        """
        Obtiene una unidad de medida por su ID.

        Args:
            unit_id (int): ID de la unidad de medida.

        Returns:
            Optional[UnitOfMeasure]: La unidad de medida si se encuentra, None en caso contrario.
        """
        return self.db.query(UnitOfMeasure).filter(UnitOfMeasure.id == unit_id).first()
    
    def get_unit_category_by_id(self, unit_category_id: int) -> Optional[UnitCategory]:
        """
        Obtiene una categoría de unidad de medida por su ID.

        Args:
            unit_category_id (int): ID de la categoría de unidad de medida.

        Returns:
            Optional[UnitCategory]: La categoría de unidad de medida si se encuentra, None en caso contrario.
        """
        return self.db.query(UnitCategory).filter(UnitCategory.id == unit_category_id).first()