from sqlalchemy.orm import Session
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

    def create_plot(self, plot_data: PlotCreate, current_user: UserInDB) -> SuccessResponse:
        # Verificar si el usuario tiene permisos para crear lotes
        if not self.user_can_create_plot(current_user):
            raise InsufficientPermissionsException()
            
        if not self.user_has_access_to_farm(current_user.id, plot_data.finca_id):
            raise DomainException(
                message="No tienes acceso a esta finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )

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

    def user_can_create_plot(self, user: UserInDB) -> bool:
        # Implementar la lógica para verificar si el usuario puede crear lotes
        allowed_roles = ["Superusuario", "Administrador de Finca"]
        return any(role.nombre in allowed_roles for role in user.roles)

    def validate_plot_data(self, plot_data: PlotCreate):
        # Implementar validaciones adicionales si es necesario
        if plot_data.area <= 0:
            raise DomainException(
                message="El área del lote debe ser mayor que cero.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        # Agregar más validaciones según sea necesario
        
    def user_has_access_to_farm(self, user_id: int, finca_id: int) -> bool:
        return self.plot_repository.check_user_farm_access(user_id, finca_id)