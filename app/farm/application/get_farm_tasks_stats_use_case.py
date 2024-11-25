from datetime import datetime, date
from typing import Optional
from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.farm.application.services.farm_service import FarmService
from app.farm.domain.schemas import FarmTasksStatsResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class GetFarmTasksStatsUseCase:
    """Caso de uso para obtener estadísticas de tareas de una finca.

    Esta clase maneja la lógica de negocio necesaria para obtener las estadísticas
    de tareas asignadas y completadas en una finca específica.

    Attributes:
        db (Session): Sesión de base de datos.
        farm_repository (FarmRepository): Repositorio para operaciones con fincas.
        cultural_practices_repository (CulturalPracticesRepository): Repositorio para operaciones con prácticas culturales.
        farm_service (FarmService): Servicio para lógica de negocio de fincas.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias."""
        self.db = db
        self.farm_repository = FarmRepository(db)
        self.cultural_practices_repository = CulturalPracticesRepository(db)
        self.farm_service = FarmService(db)

    def get_farm_tasks_stats(
        self, 
        farm_id: int, 
        current_user: UserInDB,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> FarmTasksStatsResponse:
        """Obtiene las estadísticas de tareas de una finca.

        Args:
            farm_id (int): ID de la finca.
            current_user (UserInDB): Usuario actual autenticado.
            start_date (Optional[date]): Fecha inicial del rango.
            end_date (Optional[date]): Fecha final del rango.

        Returns:
            FarmTasksStatsResponse: Estadísticas de tareas de la finca.

        Raises:
            DomainException: Si la finca no existe o el usuario no tiene permisos.
        """
        # Validar que la finca existe
        farm = self.farm_repository.get_farm_by_id(farm_id)
        if not farm:
            raise DomainException(
                message="La finca especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Validar que el usuario es administrador de la finca
        if not self.farm_service.user_is_farm_admin(current_user.id, farm_id):
            raise DomainException(
                message="No tienes permisos para ver las estadísticas de esta finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Obtener estadísticas
        total_tasks, completed_tasks = self.cultural_practices_repository.get_farm_tasks_stats(
            farm_id, 
            start_date, 
            end_date
        )

        # Calcular tasa de completitud
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return FarmTasksStatsResponse(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            completion_rate=round(completion_rate, 2)
        ) 