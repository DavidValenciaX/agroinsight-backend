from fastapi import status
from sqlalchemy.orm import Session
from app.costs.domain.schemas import TaskCostsCreate, CostRegistrationResponse
from app.costs.infrastructure.sql_repository import CostsRepository
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.infrastructure.common.common_exceptions import DomainException
from app.user.domain.schemas import UserInDB
from app.farm.application.services.farm_service import FarmService
from app.cultural_practices.domain.schemas import NivelLaborCultural
from app.crop.infrastructure.sql_repository import CropRepository
from app.plot.infrastructure.sql_repository import PlotRepository
from decimal import Decimal

class RegisterTaskCostsUseCase:
    """Caso de uso para registrar los costos asociados a una tarea cultural."""

    def __init__(self, db: Session):
        self.db = db
        self.costs_repository = CostsRepository(db)
        self.cultural_practices_repository = CulturalPracticesRepository(db)
        self.farm_service = FarmService(db)
        self.crop_repository = CropRepository(db)
        self.plot_repository = PlotRepository(db)

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

        labor_cost_registered = False
        inputs_registered = 0
        machinery_registered = 0

        # Obtener la tarea y su nivel
        task = self.cultural_practices_repository.get_task_by_id(task_id)
        
        # Calcular el costo total de la tarea
        total_cost = Decimal('0.00')
        
        # Sumar costo de mano de obra
        if costs.labor_cost:
            labor_cost = (costs.labor_cost.cantidad_trabajadores * 
                         costs.labor_cost.horas_trabajadas * 
                         costs.labor_cost.costo_hora)
            total_cost += labor_cost

        # Sumar costos de insumos
        if costs.inputs:
            for input_data in costs.inputs:
                costo_unitario = self.costs_repository.get_input_cost(input_data.insumo_id)
                if costo_unitario:
                    total_cost += costo_unitario * input_data.cantidad_utilizada

        # Sumar costos de maquinaria
        if costs.machinery:
            for machinery_data in costs.machinery:
                costo_hora = self.costs_repository.get_machinery_cost_per_hour(
                    machinery_data.maquinaria_id
                )
                if costo_hora:
                    total_cost += costo_hora * machinery_data.horas_uso

        # Actualizar los costos según el nivel de la tarea
        if task.tipo_labor.nivel == NivelLaborCultural.CULTIVO:
            # Si es nivel cultivo, actualizar el costo de producción del cultivo activo en el lote
            active_crop = self.crop_repository.get_active_crop_by_plot_id(task.lote_id)
            if active_crop:
                self.crop_repository.update_production_cost(active_crop.id, total_cost)
        else:
            # Si es nivel lote, actualizar los costos de mantenimiento del lote
            self.plot_repository.update_maintenance_costs(task.lote_id, total_cost)

        # Registrar costo de mano de obra
        if costs.labor_cost:
            labor_cost_registered = self.costs_repository.create_labor_cost(
                task_id, costs.labor_cost
            )

        # Registrar costos de insumos
        if costs.inputs:
            for input_data in costs.inputs:
                costo_unitario = self.costs_repository.get_input_cost(input_data.insumo_id)
                if not costo_unitario:
                    continue
                
                costo_total = costo_unitario * input_data.cantidad_utilizada
                if self.costs_repository.create_task_input(task_id, input_data, costo_total):
                    inputs_registered += 1

        # Registrar costos de maquinaria
        if costs.machinery:
            for machinery_data in costs.machinery:
                costo_hora = self.costs_repository.get_machinery_cost_per_hour(
                    machinery_data.maquinaria_id
                )
                if not costo_hora:
                    continue
                
                costo_total = costo_hora * machinery_data.horas_uso
                if self.costs_repository.create_task_machinery(task_id, machinery_data, costo_total):
                    machinery_registered += 1

        return CostRegistrationResponse(
            message="Costos registrados exitosamente",
            labor_cost_registered=labor_cost_registered,
            inputs_registered=inputs_registered,
            machinery_registered=machinery_registered
        )