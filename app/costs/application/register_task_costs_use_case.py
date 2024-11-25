from fastapi import status
from sqlalchemy.orm import Session
from app.costs.domain.schemas import TaskCostsCreate, CostRegistrationResponse
from app.costs.infrastructure.sql_repository import CostsRepository
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.infrastructure.common.common_exceptions import DomainException
from app.user.domain.schemas import UserInDB
from app.farm.application.services.farm_service import FarmService
from app.crop.infrastructure.sql_repository import CropRepository
from app.plot.infrastructure.sql_repository import PlotRepository
from app.measurement.application.services.measurement_service import MeasurementService

class RegisterTaskCostsUseCase:
    """Caso de uso para registrar los costos asociados a una tarea cultural."""

    def __init__(self, db: Session):
        self.db = db
        self.costs_repository = CostsRepository(db)
        self.cultural_practices_repository = CulturalPracticesRepository(db)
        self.farm_service = FarmService(db)
        self.crop_repository = CropRepository(db)
        self.plot_repository = PlotRepository(db)
        self.measurement_service = MeasurementService(db)

    def register_costs(self, task_id: int, farm_id: int, costs: TaskCostsCreate, current_user: UserInDB) -> CostRegistrationResponse:
        """Registra los costos asociados a una tarea cultural.

        Args:
            task_id (int): ID de la tarea.
            farm_id (int): ID de la finca.
            costs (TaskCostsCreate): Datos de los costos a registrar.
            current_user (UserInDB): Usuario actual.

        Returns:
            CostRegistrationResponse: Respuesta con el resultado del registro de costos.

        Raises:
            DomainException: Si hay errores de validación o permisos.
        """
        # Validar que la tarea existe
        task = self.cultural_practices_repository.get_task_by_id(task_id)
        if not task:
            raise DomainException(
                message="La tarea especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Validar que el usuario es administrador de la finca
        if not self.farm_service.user_is_farm_admin(current_user.id, farm_id):
            raise DomainException(
                message="No tienes permisos para registrar costos en esta finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Get default currency if needed
        default_currency = self.measurement_service.get_default_currency()

        labor_cost_registered = False
        inputs_registered = 0
        machinery_registered = 0

        # Registrar costo de mano de obra
        if costs.labor_cost:
            # Set default currency if not provided
            if costs.labor_cost.moneda_id is None:
                costs.labor_cost.moneda_id = default_currency.id
            
            labor_cost_registered = self.costs_repository.create_labor_cost(
                task_id, costs.labor_cost
            )

        # Registrar costos de insumos
        if costs.inputs:
            for input_data in costs.inputs:
                if self.costs_repository.create_task_input(task_id, input_data):
                    inputs_registered += 1

        # Registrar costos de maquinaria
        if costs.machinery:
            for machinery_data in costs.machinery:
                if self.costs_repository.create_task_machinery(task_id, machinery_data):
                    machinery_registered += 1

        return CostRegistrationResponse(
            message="Costos registrados exitosamente",
            labor_cost_registered=labor_cost_registered,
            inputs_registered=inputs_registered,
            machinery_registered=machinery_registered
        )