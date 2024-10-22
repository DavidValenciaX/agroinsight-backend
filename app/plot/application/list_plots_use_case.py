# app/plot/application/list_plots_use_case.py
from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.farm.application.services.farm_service import FarmService
from app.plot.infrastructure.sql_repository import PlotRepository
from app.plot.domain.schemas import PaginatedPlotListResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from app.infrastructure.mappers.response_mappers import map_plot_to_response
from fastapi import status
from math import ceil

class ListPlotsUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.plot_repository = PlotRepository(db)
        self.farm_repository = FarmRepository(db)
        self.farm_service = FarmService(db)

    def list_plots(self, current_user: UserInDB, farm_id: int, page: int, per_page: int) -> PaginatedPlotListResponse:
        farm = self.farm_repository.get_farm_by_id(farm_id)
        if not farm:
            raise DomainException(
                message="La finca especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        if not self.farm_service.user_is_farm_admin(current_user.id, farm_id):
            raise DomainException(
                message="No tienes permisos para obtener información de los lotes de esta finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        total_plots, plots = self.plot_repository.list_plots_by_farm_paginated(farm_id, page, per_page)

        # Usar la función de mapeo para construir PlotResponse para cada lote
        plot_responses = [map_plot_to_response(plot) for plot in plots]

        total_pages = ceil(total_plots / per_page)

        return PaginatedPlotListResponse(
            plots=plot_responses,
            total_plots=total_plots,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )