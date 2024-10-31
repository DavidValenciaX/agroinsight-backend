from sqlalchemy.orm import Session
from app.measurement.domain.schemas import UnitsListResponse
from app.measurement.infrastructure.sql_repository import MeasurementRepository

class ListUnitsUseCase:
    """
    Caso de uso para listar las unidades de medida.

    Esta clase maneja la lógica para obtener todas las unidades de medida
    del sistema con sus respectivas categorías.

    Attributes:
        db (Session): Sesión de base de datos para realizar operaciones.
        measurement_repository (MeasurementRepository): Repositorio para operaciones de medidas.
    """

    def __init__(self, db: Session):
        """
        Inicializa una nueva instancia de ListUnitsUseCase.

        Args:
            db (Session): La sesión de base de datos a utilizar.
        """
        self.db = db
        self.measurement_repository = MeasurementRepository(db)

    def list_units(self) -> UnitsListResponse:
        """
        Obtiene todas las unidades de medida del sistema.

        Este método consulta el repositorio para recuperar todas las unidades de medida
        y devuelve un objeto de respuesta que contiene la lista de unidades.

        Returns:
            UnitsListResponse: Objeto de respuesta con la lista de unidades de medida.
        """
        units = self.measurement_repository.get_all_units()
        return UnitsListResponse(
            units=units
        )
