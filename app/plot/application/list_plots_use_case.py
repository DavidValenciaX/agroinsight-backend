from sqlalchemy.orm import Session
from app.plot.infrastructure.sql_repository import PlotRepository
from app.plot.domain.schemas import PlotListResponse, PlotResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class ListPlotsUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.plot_repository = PlotRepository(db)

    def execute(self, current_user: UserInDB, finca_id: int) -> PlotListResponse:
        # Verificar si la finca existe
        farm = self.plot_repository.get_farm_by_id(finca_id)
        if not farm:
            raise DomainException(
                message="La finca especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Verificar si el usuario tiene acceso a la finca
        if not self.user_has_access_to_farm(current_user.id, finca_id):
            raise DomainException(
                message="No tienes acceso a esta finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Obtener los lotes de la finca específica
        plots = self.plot_repository.list_plots_by_farm(finca_id)

        # Construir y retornar la respuesta
        plot_responses = [
            PlotResponse(
                id=plot.id,
                nombre=plot.nombre,
                area=plot.area,
                unidad_area=plot.unidad_area.abreviatura,
                latitud=plot.latitud,
                longitud=plot.longitud,
                finca_id=plot.finca_id
            ) for plot in plots
        ]

        return PlotListResponse(plots=plot_responses)

    def user_has_access_to_farm(self, user_id: int, finca_id: int) -> bool:
        # Verificar si el usuario tiene acceso a la finca
        return self.plot_repository.check_user_farm_access(user_id, finca_id)