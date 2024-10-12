from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.plot.infrastructure.sql_repository import PlotRepository
from app.plot.domain.schemas import PlotCreate
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException, InsufficientPermissionsException
from fastapi import status

class CreatePlotUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.plot_repository = PlotRepository(db)
        self.farm_repository = FarmRepository(db)
        
    def create_plot(self, plot_data: PlotCreate, farm_id: int, current_user: UserInDB) -> SuccessResponse:
        if not current_user:
            raise MissingTokenException()
        
        if farm_id != plot_data.finca_id:
            raise DomainException(
                message="El ID de la finca en la URL no coincide con el ID de la finca en el cuerpo de la solicitud.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        #Validar si el usuario tiene permiso para crear lotes en la finca
        if not self.farm_repository.user_is_farm_admin(current_user.id, plot_data.finca_id):
            raise InsufficientPermissionsException()
        
        # Validar los datos de entrada
        self.validate_plot_data(plot_data)
        
        # Verificar si ya existe un lote con el mismo nombre en la misma finca
        existing_plot = self.plot_repository.get_plot_by_name_and_farm(plot_data.nombre, plot_data.finca_id)
        if existing_plot:
            raise DomainException(
                message="Ya existe un lote con este nombre en la finca.",
                status_code=status.HTTP_409_CONFLICT
            )

        # Crear el lote
        plot = self.plot_repository.create_plot(plot_data)
        if not plot:
            raise DomainException(
                message="No se pudo crear el lote.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return SuccessResponse(message="Lote creado exitosamente")
    
    def validate_plot_data(self, plot_data: PlotCreate):
        # Implementar validaciones adicionales si es necesario
        if plot_data.area <= 0:
            raise DomainException(
                message="El área del lote debe ser mayor que cero.",
                status_code=status.HTTP_400_BAD_REQUEST
            )