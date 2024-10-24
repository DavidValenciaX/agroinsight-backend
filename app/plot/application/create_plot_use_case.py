from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.plot.infrastructure.sql_repository import PlotRepository
from app.plot.domain.schemas import PlotCreate
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserInDB
from app.farm.application.services.farm_service import FarmService
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class CreatePlotUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.plot_repository = PlotRepository(db)
        self.farm_repository = FarmRepository(db)
        self.farm_service = FarmService(db)
        
    def create_plot(self, plot_data: PlotCreate, current_user: UserInDB) -> SuccessResponse:
        
        # Validar que la unidad de area exista
        unit_of_measure = self.farm_repository.get_unit_of_measure_by_id(plot_data.unidad_area_id)
        if not unit_of_measure:
            raise DomainException(
                message="La unidad de medida no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # validar que la unidad de medida sea de area
        if self.farm_repository.get_unit_category_by_id(unit_of_measure.categoria_id).nombre != self.farm_service.UNIT_CATEGORY_AREA_NAME:
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
            
        #Validar si el usuario tiene permiso para crear lotes en la finca
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