from sqlalchemy.orm import Session
from app.plot.infrastructure.sql_repository import PlotRepository
from app.plot.domain.schemas import PlotCreate, PlotResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class CreatePlotUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.plot_repository = PlotRepository(db)

    def execute(self, plot_data: PlotCreate, current_user: UserInDB) -> PlotResponse:
        # Verificar si el usuario tiene permisos para crear lotes
        if not self.user_can_create_plot(current_user):
            raise DomainException(
                message="No tienes permisos para crear lotes.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Validar los datos de entrada
        self.validate_plot_data(plot_data)

        # Crear el lote
        plot = self.plot_repository.create_plot(plot_data, current_user.id)
        if not plot:
            raise DomainException(
                message="No se pudo crear el lote.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Construir y retornar la respuesta
        return PlotResponse(
            id=plot.id,
            nombre=plot.nombre,
            area=plot.area,
            unidad_area=plot.unidad_area.abreviatura,
            latitud=plot.latitud,
            longitud=plot.longitud,
            finca_id=plot.finca_id
        )

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