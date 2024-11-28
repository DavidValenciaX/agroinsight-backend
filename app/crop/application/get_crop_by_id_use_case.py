from sqlalchemy.orm import Session
from decimal import Decimal
from app.crop.infrastructure.sql_repository import CropRepository
from app.crop.domain.schemas import CropResponse
from app.farm.application.services.farm_service import FarmService
from app.plot.infrastructure.sql_repository import PlotRepository
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.costs.infrastructure.sql_repository import CostsRepository
from fastapi import status

class GetCropByIdUseCase:
    """Caso de uso para obtener los detalles de un cultivo específico."""

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias."""
        self.db = db
        self.crop_repository = CropRepository(db)
        self.plot_repository = PlotRepository(db)
        self.farm_service = FarmService(db)
        self.cultural_practices_repository = CulturalPracticesRepository(db)
        self.costs_repository = CostsRepository(db)

    def get_crop(self, crop_id: int, current_user: UserInDB) -> CropResponse:
        """
        Obtiene los detalles de un cultivo específico.

        Args:
            crop_id (int): ID del cultivo a consultar.
            current_user (UserInDB): Usuario que realiza la consulta.

        Returns:
            CropResponse: Detalles del cultivo.

        Raises:
            DomainException: Si el cultivo no existe o el usuario no tiene permisos.
        """
        # Obtener el cultivo
        crop = self.crop_repository.get_crop_by_id(crop_id)
        if not crop:
            raise DomainException(
                message="El cultivo especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Obtener el lote
        plot = self.plot_repository.get_plot_by_id(crop.lote_id)
        if not plot:
            raise DomainException(
                message="No se pudo obtener el lote asociado al cultivo.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Validar que el usuario tenga permisos para ver el cultivo
        if not self.farm_service.user_is_farm_admin(current_user.id, plot.finca_id):
            raise DomainException(
                message="No tienes permisos para ver este cultivo.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Calcular ingreso total si hay datos de venta
        ingreso_total = None
        if crop.cantidad_vendida and crop.precio_venta_unitario:
            ingreso_total = Decimal(crop.cantidad_vendida) * crop.precio_venta_unitario

        # Calcular costo de producción sumando los costos de todas las tareas
        crop_tasks = self.cultural_practices_repository.get_tasks_by_crop_id(crop_id)
        total_crop_task_cost = Decimal(0)
        
        for task in crop_tasks:
            labor_cost = self.costs_repository.get_labor_cost(task.id)
            input_cost = self.costs_repository.get_task_inputs_cost(task.id)
            machinery_cost = self.costs_repository.get_task_machinery_cost(task.id)
            task_total = labor_cost + input_cost + machinery_cost
            total_crop_task_cost += task_total

        # Crear respuesta con los campos calculados
        response = CropResponse.model_validate(crop)
        response.ingreso_total = ingreso_total
        response.costo_produccion = total_crop_task_cost if total_crop_task_cost > 0 else None

        return response 