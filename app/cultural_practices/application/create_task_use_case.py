from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.domain.schemas import TareaLaborCulturalCreate
from app.user.domain.schemas import SuccessResponse, UserInDB
from app.infrastructure.common.common_exceptions import DomainException, InsufficientPermissionsException
from fastapi import status
from datetime import datetime

class CreateTaskUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)

    def execute(self, tarea_data: TareaLaborCulturalCreate, current_user: UserInDB) -> SuccessResponse:
        if not self.user_can_create_tarea(current_user):
            raise InsufficientPermissionsException()

        # Validar los datos de entrada
        self.validate_tarea_data(tarea_data)
        
        # Verificar si el tipo de labor cultural existe
        if not self.cultural_practice_repository.tipo_labor_cultural_exists(tarea_data.tipo_labor_id):
            raise DomainException(
                message="El tipo de labor cultural especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Verificar si el estado de tarea existe
        if not self.cultural_practice_repository.estado_tarea_exists(tarea_data.estado_id):
            raise DomainException(
                message="El estado de tarea especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener el nombre del estado de tarea
        estado_nombre = self.cultural_practice_repository.get_estado_tarea_nombre(tarea_data.estado_id)
        if estado_nombre == "Completada":
            raise DomainException(
                message="No se puede crear una tarea directamente en estado 'Completada'.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        # Verificar si el lote existe
        if not self.cultural_practice_repository.plot_exists(tarea_data.lote_id):
            raise DomainException(
                message="El lote especificado no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Crear la tarea
        tarea = self.cultural_practice_repository.create_tarea(tarea_data)
        if not tarea:
            raise DomainException(
                message="No se pudo crear la tarea de labor cultural.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return SuccessResponse(message="Tarea creada exitosamente")

    def user_can_create_tarea(self, user: UserInDB) -> bool:
        allowed_roles = ["Superusuario", "Administrador de Finca"]
        return any(role.nombre in allowed_roles for role in user.roles)

    def validate_tarea_data(self, tarea_data: TareaLaborCulturalCreate):
        # Obtener la fecha actual
        current_date = self.cultural_practice_repository.get_current_date()

        # Validar que la fecha programada no esté en el pasado
        if tarea_data.fecha_programada < current_date:
            raise DomainException(
                message="La fecha programada no puede ser anterior a la fecha actual.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que si hay fecha completada, no sea anterior a la fecha programada
        if tarea_data.fecha_completada and tarea_data.fecha_completada < tarea_data.fecha_programada:
            raise DomainException(
                message="La fecha de completado no puede ser anterior a la fecha programada.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
