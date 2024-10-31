from sqlalchemy.orm import Session
from app.farm.application.services.farm_service import FarmService
from app.farm.infrastructure.sql_repository import FarmRepository
from app.farm.domain.schemas import FarmCreate
from app.infrastructure.common.response_models import SuccessResponse
from app.measurement.application.services.measurement_service import MeasurementService
from app.measurement.infrastructure.sql_repository import MeasurementRepository
from app.user.application.services.user_service import UserService
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

from app.user.infrastructure.sql_repository import UserRepository

class CreateFarmUseCase:
    """Caso de uso para la creación de una nueva finca.

    Esta clase maneja la lógica de negocio necesaria para crear una nueva finca,
    incluyendo las validaciones de unidades de medida y la asignación de roles.

    Attributes:
        db (Session): Sesión de base de datos.
        farm_repository (FarmRepository): Repositorio para operaciones con fincas.
        user_repository (UserRepository): Repositorio para operaciones con usuarios.
        user_service (UserService): Servicio para lógica de negocio de usuarios.
        farm_service (FarmService): Servicio para lógica de negocio de fincas.
        measurement_service (MeasurementService): Servicio para lógica de medidas.
        measurement_repository (MeasurementRepository): Repositorio para operaciones con medidas.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        self.farm_repository = FarmRepository(db)
        self.user_repository = UserRepository(db)
        self.user_service = UserService(db)
        self.farm_service = FarmService(db)
        self.measurement_service = MeasurementService(db)
        self.measurement_repository = MeasurementRepository(db)

    def create_farm(self, farm_data: FarmCreate, current_user: UserInDB) -> SuccessResponse:
        """Crea una nueva finca y asigna al usuario actual como administrador.

        Este método realiza las siguientes validaciones:
        1. Verifica que la unidad de medida especificada exista
        2. Confirma que la unidad de medida sea de tipo área
        3. Valida que el usuario no tenga otra finca con el mismo nombre
        4. Crea la finca y asigna el rol de administrador al usuario

        Args:
            farm_data (FarmCreate): Datos de la finca a crear.
            current_user (UserInDB): Usuario que está creando la finca.

        Returns:
            SuccessResponse: Respuesta exitosa con mensaje de confirmación.

        Raises:
            DomainException: Si ocurre algún error de validación:
                - 404: La unidad de medida no existe
                - 400: La unidad de medida no es de tipo área
                - 409: El usuario ya tiene una finca con ese nombre
                - 500: Error al crear la finca
        """
        
        # Validar que la unidad de medida exista
        unit_of_measure = self.measurement_repository.get_unit_of_measure_by_id(farm_data.unidad_area_id)
        if not unit_of_measure:
            raise DomainException(
                message="La unidad de medida no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Validar que la unidad de medida sea de area
        if self.measurement_repository.get_unit_category_by_id(unit_of_measure.categoria_id).nombre != self.measurement_service.UNIT_CATEGORY_AREA_NAME:
            raise DomainException(
                message="La unidad de medida no es de área.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        existing_farm = self.farm_repository.get_farm_by_name(farm_data.nombre)
        
        if existing_farm:
            if self.farm_service.user_is_farm_admin(current_user.id, existing_farm.id):
                raise DomainException(
                    message="El usuario ya tiene una finca registrada con ese nombre. Por favor, escoja un nombre diferente.",
                    status_code=status.HTTP_409_CONFLICT
                )

        # Crear la finca
        farm = self.farm_repository.create_farm(farm_data)
        if not farm:
            raise DomainException(
                message="No se pudo crear la finca.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        admin_role = self.farm_service.get_admin_role()
        
        # Asignar el rol de administrador a la finca
        self.farm_repository.add_user_to_farm_with_role(current_user.id, farm.id, admin_role.id)

        return SuccessResponse(message="Finca creada exitosamente")
