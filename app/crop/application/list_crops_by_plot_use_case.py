from decimal import Decimal
from math import ceil
from sqlalchemy.orm import Session
from app.costs.infrastructure.sql_repository import CostsRepository
from app.crop.infrastructure.sql_repository import CropRepository
from app.crop.domain.schemas import PaginatedCropListResponse
from app.plot.infrastructure.sql_repository import PlotRepository
from app.farm.infrastructure.sql_repository import FarmRepository
from app.farm.application.services.farm_service import FarmService
from app.reports.infrastructure.sql_repository import FinancialReportRepository
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from app.user.infrastructure.sql_repository import UserRepository
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository

class ListCropsByPlotUseCase:
    """Caso de uso para listar los cultivos de un lote específico.

    Esta clase maneja la lógica de negocio necesaria para obtener una lista paginada
    de los cultivos que pertenecen a un lote específico, asegurando que el usuario
    tenga los permisos adecuados.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
        crop_repository (CropRepository): Repositorio para operaciones con cultivos.
        plot_repository (PlotRepository): Repositorio para operaciones con lotes.
        farm_repository (FarmRepository): Repositorio para operaciones con fincas.
        farm_service (FarmService): Servicio para lógica de negocio de fincas.
        user_repository (UserRepository): Repositorio para operaciones con usuarios.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        self.crop_repository = CropRepository(db)
        self.plot_repository = PlotRepository(db)
        self.farm_repository = FarmRepository(db)
        self.farm_service = FarmService(db)
        self.user_repository = UserRepository(db)
        self.financial_report_repository = FinancialReportRepository(db)
        self.cultural_practices_repository = CulturalPracticesRepository(db)
        self.costs_repository = CostsRepository(db)
        
    def list_crops(self, plot_id: int, page: int, per_page: int, current_user: UserInDB) -> PaginatedCropListResponse:
        """Lista los cultivos de un lote específico de forma paginada.

        Este método realiza las siguientes validaciones:
        1. Verifica si el lote especificado existe.
        2. Obtiene la finca asociada al lote y verifica su existencia.
        3. Verifica que el usuario tenga acceso a la finca.

        Args:
            plot_id (int): ID del lote del cual se quieren listar los cultivos.
            page (int): Número de página actual para la paginación.
            per_page (int): Cantidad de cultivos por página.
            current_user (UserInDB): Usuario que está solicitando la lista de cultivos.

        Returns:
            PaginatedCropListResponse: Respuesta paginada que incluye:
                - Lista de cultivos para la página actual.
                - Total de cultivos.
                - Número de página actual.
                - Cantidad de elementos por página.
                - Total de páginas.

        Raises:
            DomainException: Si ocurre algún error de validación:
                - 404: El lote o la finca no existen.
                - 403: El usuario no tiene permisos para ver los cultivos de este lote.
        """
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
        user = self.user_repository.get_user_by_id(current_user.id)
        if not user:
            raise DomainException(
                message="No se pudo obtener el usuario.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        nombre_usuario = user.nombre + " " + user.apellido
        if not self.farm_service.user_is_farm_admin(user.id, farm.id):
            raise DomainException(
                message=f"El usuario {nombre_usuario} con email {user.email} no tiene permisos para ver los cultivos de este lote.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Obtener los cultivos
        total_crops, crops = self.crop_repository.get_crops_by_plot_id_paginated(plot_id, page, per_page)
        
        # Agregar los campos de ingreso total y costo de producción
        for crop in crops:
            crop.ingreso_total = crop.precio_venta_unitario * crop.cantidad_vendida if crop.precio_venta_unitario and crop.cantidad_vendida else None
            
            crop_tasks = self.cultural_practices_repository.get_tasks_by_crop_id(crop.id)
            total_crop_task_cost = Decimal(0)
            
            for task in crop_tasks:
                labor_cost, input_cost, machinery_cost = self.costs_repository.get_task_costs(task.id)
                task_total = labor_cost + input_cost + machinery_cost
                total_crop_task_cost += task_total
            
            crop.costo_produccion = total_crop_task_cost if total_crop_task_cost else None
        
        total_pages = ceil(total_crops / per_page)
        
        return PaginatedCropListResponse(
            crops=crops,
            total_crops=total_crops,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )

