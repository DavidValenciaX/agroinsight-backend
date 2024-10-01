# app/plot/application/list_plots_use_case.py
from sqlalchemy.orm import Session
from app.plot.infrastructure.sql_repository import PlotRepository
from app.plot.domain.schemas import PlotResponse, PaginatedPlotListResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from app.infrastructure.mappers.response_mappers import map_plot_to_response
from fastapi import status
from math import ceil

class ListPlotsUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.plot_repository = PlotRepository(db)

    def execute(self, current_user: UserInDB, finca_id: int, page: int, per_page: int) -> PaginatedPlotListResponse:
        farm = self.plot_repository.get_farm_by_id(finca_id)
        if not farm:
            raise DomainException(
                message="La finca especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        if not self.user_has_access_to_farm(current_user.id, finca_id):
            raise DomainException(
                message="No tienes acceso a esta finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        total_plots, plots = self.plot_repository.list_plots_by_farm_paginated(finca_id, page, per_page)

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

    def user_has_access_to_farm(self, user_id: int, finca_id: int) -> bool:
        return self.plot_repository.check_user_farm_access(user_id, finca_id)