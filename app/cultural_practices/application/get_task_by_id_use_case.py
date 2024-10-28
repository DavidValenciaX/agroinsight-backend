from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.domain.schemas import TaskResponse
from app.farm.application.services.farm_service import FarmService
from app.farm.infrastructure.sql_repository import FarmRepository
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from app.user.domain.schemas import UserInDB

class GetTaskByIdUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)
        self.farm_service = FarmService(db)
        self.farm_repository = FarmRepository(db)
        
    def get_task_by_id(self, farm_id: int, task_id: int, current_user: UserInDB) -> TaskResponse:
        # Validar que la tarea existe
        task = self.cultural_practice_repository.get_task_by_id(task_id)
        if not task:
            raise DomainException(
                message="La tarea especificada no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Validar que el usuario es el administrador de la finca
        if not self.farm_service.user_is_farm_admin(current_user.id, farm_id):
            raise DomainException(
                message="No tienes permisos para acceder a esta tarea.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        return TaskResponse(
            id=task.id,
            nombre=task.nombre,
            tipo_labor_id=task.tipo_labor_id,
            fecha_inicio_estimada=task.fecha_inicio_estimada,
            fecha_finalizacion=task.fecha_finalizacion,
            descripcion=task.descripcion,
            estado_id=task.estado_id,
            lote_id=task.lote_id
        )

