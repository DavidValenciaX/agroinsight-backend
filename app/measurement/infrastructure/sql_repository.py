from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.measurement.infrastructure.orm_models import UnitOfMeasure, UnitCategory
from app.measurement.domain.schemas import UnitOfMeasureResponse

class MeasurementRepository:
    """Repositorio para gestionar las operaciones relacionadas con unidades de medida.

    Este repositorio proporciona métodos para interactuar con las unidades de medida y sus categorías
    en la base de datos.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
    """

    def __init__(self, db: Session):
        """Inicializa el repositorio con la sesión de base de datos.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db

    def get_all_units(self) -> List[UnitOfMeasureResponse]:
        """Obtiene todas las unidades de medida con sus categorías.

        Este método consulta la base de datos para recuperar todas las unidades de medida y sus
        categorías asociadas.

        Returns:
            List[UnitOfMeasureResponse]: Lista de todas las unidades de medida con sus categorías.
        """
        units = self.db.query(UnitOfMeasure).options(
            joinedload(UnitOfMeasure.categoria)
        ).all()
        return [UnitOfMeasureResponse.model_validate(unit) for unit in units]

    def get_unit_of_measure_by_id(self, unit_id: int) -> Optional[UnitOfMeasure]:
        """Obtiene una unidad de medida por su ID.

        Este método consulta la base de datos para recuperar una unidad de medida específica
        utilizando su ID.

        Args:
            unit_id (int): ID de la unidad de medida.

        Returns:
            Optional[UnitOfMeasure]: La unidad de medida si se encuentra, None en caso contrario.
        """
        return self.db.query(UnitOfMeasure).filter(UnitOfMeasure.id == unit_id).first()
    
    def get_unit_of_measure_by_name(self, unit_name: str) -> Optional[UnitOfMeasure]:
        """Obtiene una unidad de medida por su nombre.

        Este método consulta la base de datos para recuperar una unidad de medida específica
        utilizando su nombre.

        Args:
            unit_name (str): Nombre de la unidad de medida.
        """
        return self.db.query(UnitOfMeasure).filter(UnitOfMeasure.nombre == unit_name).first()
    
    def get_unit_category_by_id(self, unit_category_id: int) -> Optional[UnitCategory]:
        """Obtiene una categoría de unidad de medida por su ID.

        Este método consulta la base de datos para recuperar una categoría de unidad de medida
        específica utilizando su ID.

        Args:
            unit_category_id (int): ID de la categoría de unidad de medida.

        Returns:
            Optional[UnitCategory]: La categoría de unidad de medida si se encuentra, None en caso contrario.
        """
        return self.db.query(UnitCategory).filter(UnitCategory.id == unit_category_id).first()
    
    def get_unit_category_by_name(self, unit_category_name: str) -> Optional[UnitCategory]:
        """Obtiene una categoría de unidad de medida por su nombre.

        Este método consulta la base de datos para recuperar una categoría de unidad de medida
        específica utilizando su nombre.

        Args:
            unit_category_name (str): Nombre de la categoría de unidad de medida.

        Returns:
            Optional[UnitCategory]: La categoría de unidad de medida si se encuentra, None en caso contrario.
        """
        return self.db.query(UnitCategory).filter(UnitCategory.nombre == unit_category_name).first()
