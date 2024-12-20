from sqlalchemy.orm import Session
from app.crop.infrastructure.sql_repository import CropRepository
from app.crop.application.services.crop_service import CropService
from app.crop.domain.schemas import CropHarvestUpdate
from app.plot.infrastructure.sql_repository import PlotRepository
from app.farm.infrastructure.sql_repository import FarmRepository
from app.farm.application.services.farm_service import FarmService
from app.measurement.application.services.measurement_service import MeasurementService
from app.measurement.infrastructure.sql_repository import MeasurementRepository
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from app.infrastructure.common.response_models import SuccessResponse
from fastapi import status
from typing import Optional

class UpdateCropHarvestUseCase:
    """Caso de uso para actualizar la información de cosecha de un cultivo."""

    def __init__(self, db: Session):
        self.db = db
        self.crop_repository = CropRepository(db)
        self.crop_service = CropService()
        self.plot_repository = PlotRepository(db)
        self.farm_repository = FarmRepository(db)
        self.farm_service = FarmService(db)
        self.measurement_service = MeasurementService(db)
        self.measurement_repository = MeasurementRepository(db)

    def update_harvest(self, crop_id: int, harvest_data: CropHarvestUpdate, current_user: UserInDB) -> SuccessResponse:
        """Actualiza la información de cosecha y venta de un cultivo.

        Args:
            crop_id (int): ID del cultivo a actualizar.
            harvest_data (CropHarvestUpdate): Datos de la cosecha y venta.
            current_user (UserInDB): Usuario que realiza la actualización.

        Returns:
            SuccessResponse: Mensaje de éxito.

        Raises:
            DomainException: Si hay errores de validación o permisos.
        """
        # Obtener el cultivo
        crop = self.crop_repository.get_crop_by_id(crop_id)
        if not crop:
            raise DomainException(
                message="El cultivo especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Obtener el lote y la finca
        plot = self.plot_repository.get_plot_by_id(crop.lote_id)
        if not plot:
            raise DomainException(
                message="No se pudo obtener el lote asociado al cultivo.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        farm = self.farm_repository.get_farm_by_id(plot.finca_id)
        if not farm:
            raise DomainException(
                message="No se pudo obtener la finca asociada al cultivo.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Verificar permisos
        if not self.farm_service.user_is_farm_admin(current_user.id, farm.id):
            raise DomainException(
                message="No tienes permisos para actualizar este cultivo.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Si no se especifica moneda, usar COP por defecto
        if harvest_data.moneda_id is None:
            default_currency = self.measurement_service.get_default_currency()
            if not default_currency:
                raise DomainException(
                    message="No se pudo obtener la moneda por defecto (COP).",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            harvest_data.moneda_id = default_currency.id

        # Validar unidades de medida
        for unit_id in [
            harvest_data.produccion_total_unidad_id,
            harvest_data.cantidad_vendida_unidad_id
        ]:
            if not self.measurement_repository.get_unit_of_measure_by_id(unit_id):
                raise DomainException(
                    message=f"La unidad de medida con ID {unit_id} no existe.",
                    status_code=status.HTTP_404_NOT_FOUND
                )

        # Validar que la moneda sea una unidad de medida válida
        currency = self.measurement_repository.get_unit_of_measure_by_id(harvest_data.moneda_id)
        if not currency:
            raise DomainException(
                message="La moneda especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar que la unidad de medida sea de tipo moneda
        currency_category = self.measurement_repository.get_unit_category_by_id(currency.categoria_id)
        if not currency_category or currency_category.nombre != self.measurement_service.UNIT_CATEGORY_CURRENCY_NAME:
            raise DomainException(
                message="La unidad de medida especificada no es una moneda válida.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        # Obtener el estado "Cosechado"
        estado_cosechado = self.crop_repository.get_crop_state_by_name(self.crop_service.COSECHADO)
        if not estado_cosechado:
            raise DomainException(
                message="No se pudo obtener el estado 'Cosechado'.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Actualizar el cultivo
        updated_crop = self.crop_repository.update_crop_harvest(crop_id, harvest_data, estado_cosechado.id)
        if not updated_crop:
            raise DomainException(
                message="Error al actualizar la información de cosecha.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return SuccessResponse(message="Información de cosecha actualizada exitosamente")