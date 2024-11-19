from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.measurement.application.services.measurement_service import MeasurementService
from app.measurement.infrastructure.sql_repository import MeasurementRepository
from app.plot.infrastructure.sql_repository import PlotRepository
from app.plot.domain.schemas import PlotCreate
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserInDB
from app.farm.application.services.farm_service import FarmService
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class CreatePlotUseCase:
    """Caso de uso para crear un nuevo lote.

    Esta clase maneja la lógica de negocio necesaria para crear un lote en una finca,
    incluyendo validaciones de permisos y existencia de recursos.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
        plot_repository (PlotRepository): Repositorio para operaciones con lotes.
        farm_repository (FarmRepository): Repositorio para operaciones con fincas.
        farm_service (FarmService): Servicio para lógica de negocio de fincas.
        measurement_service (MeasurementService): Servicio para lógica de negocio de medidas.
        measurement_repository (MeasurementRepository): Repositorio para operaciones con medidas.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        self.plot_repository = PlotRepository(db)
        self.farm_repository = FarmRepository(db)
        self.farm_service = FarmService(db)
        self.measurement_service = MeasurementService(db)
        self.measurement_repository = MeasurementRepository(db)
        
    def create_plot(self, plot_data: PlotCreate, current_user: UserInDB) -> SuccessResponse:
        """Crea un nuevo lote en la base de datos.

        Este método realiza las siguientes validaciones antes de crear el lote:
        1. Verifica que la unidad de medida exista.
        2. Confirma que la unidad de medida sea de tipo área.
        3. Verifica que la finca exista.
        4. Valida que el usuario tenga permisos para crear lotes en la finca.
        5. Asegura que no exista un lote con el mismo nombre en la finca.
        6. Comprueba que el área del lote no exceda el área total de la finca.

        Args:
            plot_data (PlotCreate): Datos del lote a crear.
            current_user (UserInDB): Usuario que está creando el lote.

        Returns:
            SuccessResponse: Respuesta exitosa con un mensaje de confirmación.

        Raises:
            DomainException: Si ocurre algún error de validación:
                - 404: La unidad de medida o la finca no existen.
                - 400: La unidad de medida no es de área o el área del lote excede la del finca.
                - 403: El usuario no tiene permisos para crear lotes en la finca.
                - 409: Ya existe un lote con el mismo nombre en la finca.
                - 500: Error al crear el lote.
        """
        # Validar que la unidad de area exista
        unit_of_measure = self.measurement_repository.get_unit_of_measure_by_id(plot_data.unidad_area_id)
        if not unit_of_measure:
            raise DomainException(
                message="La unidad de medida no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Obtener el ID de la moneda COP
        cop_currency = self.measurement_repository.get_unit_of_measure_by_name(
            self.measurement_service.UNIT_COP
        )
        if not cop_currency:
            raise DomainException(
                message="No se encontró la moneda COP en el sistema.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        # Asignar la moneda COP al plot_data
        plot_data.moneda_id = cop_currency.id
            
        # validar que la unidad de medida sea de area
        if self.measurement_repository.get_unit_category_by_id(unit_of_measure.categoria_id).nombre != self.measurement_service.UNIT_CATEGORY_AREA_NAME:
            raise DomainException(
                message="La unidad de medida no es de área.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        # validar que la finca exista
        farm = self.farm_repository.get_farm_by_id(plot_data.finca_id)
        if not farm:
            raise DomainException(
                message="La finca no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Validar si el usuario tiene permiso para crear lotes en la finca
        if not self.farm_service.user_is_farm_admin(current_user.id, farm.id):
            raise DomainException(
                message="No tienes permisos para crear lotes en esta finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar si ya existe un lote con el mismo nombre en la misma finca
        existing_plot = self.plot_repository.get_plot_by_name_and_farm(plot_data.nombre, farm.id)
        if existing_plot:
            raise DomainException(
                message="Ya existe un lote con este nombre en la finca.",
                status_code=status.HTTP_409_CONFLICT
            )
            
        # validar que el area del lote que se quiere crear no exceda el area de la finca
        if plot_data.area > farm.area_total:
            raise DomainException(
                message="El área del lote que se quiere crear no puede ser mayor al área de la finca.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Crear el lote
        plot = self.plot_repository.create_plot(plot_data)
        if not plot:
            raise DomainException(
                message="No se pudo crear el lote.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return SuccessResponse(message="Lote creado exitosamente")