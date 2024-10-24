from math import ceil
from sqlalchemy.orm import Session
from app.crop.infrastructure.sql_repository import CropRepository
from app.crop.domain.schemas import PaginatedCropListResponse
from app.plot.infrastructure.sql_repository import PlotRepository
from app.farm.infrastructure.sql_repository import FarmRepository
from app.farm.application.services.farm_service import FarmService
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class ListCropsByPlotUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.crop_repository = CropRepository(db)
        self.plot_repository = PlotRepository(db)
        self.farm_repository = FarmRepository(db)
        self.farm_service = FarmService(db)

    def list_crops(self, plot_id: int, page: int, per_page: int, current_user: UserInDB) -> PaginatedCropListResponse:
        # Verificar si el lote existe
        plot = self.plot_repository.get_plot_by_id(plot_id)
        if not plot:
            raise DomainException(
                message="El lote especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Obtener la finca asociada al lote
        farm = self.farm_repository.get_farm_by_id(plot.finca_id)
        if not farm:
            raise DomainException(
                message="No se pudo obtener la finca asociada al lote.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Verificar que el usuario tenga acceso a la finca
        if not self.farm_service.user_is_farm_admin(current_user.id, farm.id):
            raise DomainException(
                message="No tienes permisos para ver los cultivos de este lote.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Obtener los cultivos
        total_crops, crops = self.crop_repository.get_crops_by_plot_id_paginated(plot_id, page, per_page)
        
        total_pages = ceil(total_crops / per_page)
        
        return PaginatedCropListResponse(
            crops=crops,
            total_crops=total_crops,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )

