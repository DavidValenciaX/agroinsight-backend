from sqlalchemy.orm import Session
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository
from app.cultural_practices.domain.schemas import AssignmentCreate, AssignmentCreateSingle
from app.farm.application.services.farm_service import FarmService
from app.infrastructure.common.response_models import MultipleResponse
from app.plot.infrastructure.sql_repository import PlotRepository
from app.farm.infrastructure.sql_repository import FarmRepository
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from app.user.infrastructure.sql_repository import UserRepository

class AssignTaskUseCase:
    """Caso de uso para asignar tareas de labor cultural a usuarios.

    Este caso de uso gestiona la lógica de negocio para la creación de asignaciones de tareas,
    asegurando que se cumplan las validaciones necesarias antes de realizar la asignación.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
        cultural_practice_repository (CulturalPracticesRepository): Repositorio para operaciones de prácticas culturales.
        user_repository (UserRepository): Repositorio para operaciones de usuarios.
        plot_repository (PlotRepository): Repositorio para operaciones de lotes.
        farm_repository (FarmRepository): Repositorio para operaciones de fincas.
        farm_service (FarmService): Servicio para lógica de negocio de fincas.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)
        self.user_repository = UserRepository(db)
        self.plot_repository = PlotRepository(db)
        self.farm_repository = FarmRepository(db)
        self.farm_service = FarmService(db)

    def create_assignment(self, assignment_data: AssignmentCreate, current_user: UserInDB) -> MultipleResponse:
        """Crea asignaciones de tareas para los usuarios especificados.

        Este método valida la existencia de la tarea, el lote y la finca, así como los permisos del usuario
        que intenta realizar la asignación. Luego, itera sobre los IDs de los usuarios y crea las asignaciones
        correspondientes, registrando los mensajes de éxito o error.

        Args:
            assignment_data (AssignmentCreate): Datos de la asignación a crear.
            current_user (UserInDB): Usuario actual autenticado que intenta realizar la asignación.

        Returns:
            MultipleResponse: Respuesta que incluye mensajes sobre el resultado de las asignaciones y el código de estado.

        Raises:
            DomainException: Si la tarea, lote o finca no existen, o si el usuario no tiene permisos.
        """
        # Validar que la tarea existe
        task = self.cultural_practice_repository.get_task_by_id(assignment_data.tarea_labor_cultural_id)
        if not task:
            raise DomainException(
                message="No se pudo obtener la tarea.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener lote por ID
        plot = self.plot_repository.get_plot_by_id(task.lote_id)
        if not plot:
            raise DomainException(
                message="No se pudo obtener el lote.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener finca por ID
        farm = self.farm_repository.get_farm_by_id(plot.finca_id)
        if not farm:
            raise DomainException(
                message="No se pudo obtener la finca.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Validar que el usuario sea administrador de la finca
        if not self.farm_service.user_is_farm_admin(current_user.id, farm.id):
            raise DomainException(
                message="No tienes permisos para asignar tareas en esta finca.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        messages = []
        success_count = 0
        failure_count = 0

        # Iterar sobre cada usuario_id en usuario_ids
        for usuario_id in assignment_data.usuario_ids:
            # Obtener el nombre del usuario
            user = self.user_repository.get_user_by_id(usuario_id)
            if not user:
                messages.append(f"El usuario con ID {usuario_id} especificado no existe.")
                failure_count += 1
                continue
            
            user_name = user.nombre + " " + user.apellido
            
            if current_user.id == usuario_id:
                messages.append(f"El usuario {user_name} es el administrador de la finca.")
                failure_count += 1
                continue
            
            # Validar que el usuario es trabajador de la finca
            if not self.farm_service.user_is_farm_worker(usuario_id, farm.id):
                messages.append(f"El usuario {user_name} no es trabajador de la finca.")
                failure_count += 1
                continue
            
            # Validar que el usuario no tenga ya asignada esa tarea
            if self.cultural_practice_repository.get_user_task_assignment(usuario_id, assignment_data.tarea_labor_cultural_id):
                messages.append(f"El usuario {user_name} ya tiene asignada la tarea con ID {assignment_data.tarea_labor_cultural_id}.")
                failure_count += 1
                continue
            
            assignment_data_single = AssignmentCreateSingle(
                usuario_id=usuario_id,
                tarea_labor_cultural_id=assignment_data.tarea_labor_cultural_id
            )
            
            if not self.cultural_practice_repository.create_assignment(assignment_data_single):
                messages.append(f"No se pudo crear la asignación para el usuario {user_name}.")
                failure_count += 1
                continue
                
            messages.append(f"Asignación creada exitosamente para el usuario {user_name}.")
            success_count += 1

        if success_count > 0 and failure_count > 0:
            status_code = status.HTTP_207_MULTI_STATUS
        elif success_count == 0:
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_200_OK

        return MultipleResponse(messages=messages, status_code=status_code)
