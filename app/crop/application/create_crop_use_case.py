from sqlalchemy.orm import Session
from app.crop.infrastructure.sql_repository import CropRepository
from app.crop.domain.schemas import CropCreate
from app.farm.application.services.farm_service import FarmService
from app.infrastructure.common.response_models import SuccessResponse
from app.plot.infrastructure.sql_repository import PlotRepository
from app.farm.infrastructure.sql_repository import FarmRepository
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class CreateCropUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.crop_repository = CropRepository(db)
        self.plot_repository = PlotRepository(db)
        self.farm_repository = FarmRepository(db)
        self.farm_service = FarmService(db)
        
    def create_crop(self, crop_data: CropCreate, current_user: UserInDB) -> SuccessResponse:
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
        if not self.crop_repository.get_unit_of_measure_by_id(crop_data.densidad_siembra_unidad_id):
            raise DomainException(
                message="La unidad de medida para densidad de siembra especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
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

