from sqlalchemy.orm import Session
from app.crop.infrastructure.sql_repository import CropRepository
from app.crop.domain.schemas import CropCreate
from app.farm.application.services.farm_service import FarmService
from app.infrastructure.common.response_models import SuccessResponse
from app.measurement.application.services.measurement_service import MeasurementService
from app.measurement.infrastructure.sql_repository import MeasurementRepository
from app.plot.infrastructure.sql_repository import PlotRepository
from app.farm.infrastructure.sql_repository import FarmRepository
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class CreateCropUseCase:
    """Caso de uso para crear un nuevo cultivo.

    Esta clase maneja la lógica de negocio necesaria para crear un cultivo en un lote,
    incluyendo validaciones de permisos y existencia de recursos.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
        crop_repository (CropRepository): Repositorio para operaciones con cultivos.
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
        self.crop_repository = CropRepository(db)
        self.plot_repository = PlotRepository(db)
        self.farm_repository = FarmRepository(db)
        self.farm_service = FarmService(db)
        self.measurement_service = MeasurementService(db)
        self.measurement_repository = MeasurementRepository(db)
        
    def create_crop(self, crop_data: CropCreate, current_user: UserInDB) -> SuccessResponse:
        """Crea un nuevo cultivo en la base de datos.

        Este método realiza las siguientes validaciones antes de crear el cultivo:
        1. Verifica que el lote especificado exista.
        2. Obtiene la finca asociada al lote y verifica su existencia.
        3. Valida que el usuario tenga permisos para crear cultivos en la finca.
        4. Verifica que la variedad de maíz especificada exista.
        5. Verifica que la unidad de medida para la densidad de siembra exista y sea válida.
        6. Verifica que el estado del cultivo especificado exista.
        7. Verifica que no exista un cultivo activo en el lote.

        Args:
            crop_data (CropCreate): Datos del cultivo a crear.
            current_user (UserInDB): Usuario que está creando el cultivo.

        Returns:
            SuccessResponse: Respuesta exitosa con un mensaje de confirmación.

        Raises:
            DomainException: Si ocurre algún error de validación:
                - 404: El lote, la finca, la variedad de maíz, la unidad de medida o el estado del cultivo no existen.
                - 403: El usuario no tiene permisos para crear cultivos en la finca.
                - 409: Ya existe un cultivo activo en el lote.
                - 500: Error al crear el cultivo.
        """
        # Obtener el lote
        plot = self.plot_repository.get_plot_by_id(crop_data.lote_id)
        if not plot:
            raise DomainException(
                message="No se pudo obtener el lote especificado.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener la finca asociada al lote
        farm = self.farm_repository.get_farm_by_id(plot.finca_id)
        if not farm:
            raise DomainException(
                message="No se pudo obtener la finca asociada al lote.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Validar que el usuario sea administrador de la finca
        if not self.farm_service.user_is_farm_admin(current_user.id, farm.id):
            raise DomainException(
                message="No tienes permisos para crear cultivos en esta finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar si la variedad de maíz existe
        if not self.crop_repository.get_corn_variety_by_id(crop_data.variedad_maiz_id):
            raise DomainException(
                message="La variedad de maíz especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Verificar si la unidad de medida para densidad de siembra existe
        unit_of_measure = self.measurement_repository.get_unit_of_measure_by_id(crop_data.densidad_siembra_unidad_id)
        if not unit_of_measure:
            raise DomainException(
                message="La unidad de medida para densidad de siembra especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # verificar que la unidad de medida para densidad de siembra sea de densidad de siembra
        unit_category = self.measurement_repository.get_unit_category_by_id(unit_of_measure.categoria_id)
        if not unit_category:
            raise DomainException(
                message="No se pudo obtener la categoría de la unidad de medida para densidad de siembra.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if unit_category.nombre != self.measurement_service.UNIT_CATEGORY_PLANTING_DENSITY_NAME:
            raise DomainException(
                message="La unidad de medida elegida no es de densidad de siembra.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        # Verificar si el estado del cultivo existe
        if not self.crop_repository.get_crop_state_by_id(crop_data.estado_id):
            raise DomainException(
                message="El estado de cultivo especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Verificar si ya existe un cultivo activo en el lote
        if self.crop_repository.has_active_crop(crop_data.lote_id):
            raise DomainException(
                message="Ya existe un cultivo activo en este lote.",
                status_code=status.HTTP_409_CONFLICT
            )

        # Crear el cultivo
        crop = self.crop_repository.create_crop(crop_data)
        if not crop:
            raise DomainException(
                message="No se pudo crear el cultivo.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return SuccessResponse(message="Cultivo creado exitosamente")

