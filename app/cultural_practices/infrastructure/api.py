"""
Este módulo define las rutas de la API para la gestión de prácticas culturales.

Incluye endpoints para la creación de tareas y asignaciones, así como para listar asignaciones.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.cultural_practices.application.get_task_by_id_use_case import GetTaskByIdUseCase
from app.cultural_practices.application.list_task_types_by_level_use_case import ListTaskTypesByLevelUseCase
from app.cultural_practices.domain.schemas import AssignmentCreate, TaskCreate, PaginatedTaskListResponse, SuccessTaskCreateResponse, TaskResponse, TaskStateListResponse, TaskTypeListResponse
from app.cultural_practices.application.assign_task_use_case import AssignTaskUseCase
from app.cultural_practices.application.create_task_use_case import CreateTaskUseCase
from app.infrastructure.common.common_exceptions import DomainException
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.infrastructure.common.response_models import MultipleResponse, SuccessResponse
from app.user.domain.schemas import UserInDB
from app.cultural_practices.application.list_tasks_by_user_and_farm_use_case import ListTasksByUserAndFarmUseCase
from app.cultural_practices.application.change_task_state_use_case import ChangeTaskStateUseCase
from app.cultural_practices.application.list_task_states_use_case import ListTaskStatesUseCase
from app.cultural_practices.application.list_task_types_use_case import ListTaskTypesUseCase
from app.cultural_practices.application.list_worker_tasks_use_case import ListWorkerTasksUseCase
from typing import Union
from app.cultural_practices.application.list_tasks_by_plot_use_case import ListTasksByPlotUseCase
from app.logs.application.decorators.log_decorator import log_activity
from app.logs.domain.schemas import LogSeverity
from app.logs.application.services.log_service import LogActionType
from app.cultural_practices.domain.schemas import NivelLaborCultural

router = APIRouter(tags=["cultural practices"])

@router.post("/task/create", response_model=SuccessTaskCreateResponse, status_code=status.HTTP_201_CREATED)
@log_activity(
    action_type=LogActionType.REGISTER_TASK,
    table_name="tarea_labor_cultural",
    severity=LogSeverity.INFO,
    description="Registro de nueva tarea de labor cultural con detalles de tipo, descripción, fecha, lote y estado",
    get_record_id=lambda *args, **kwargs: kwargs.get('result').task_id if kwargs.get('result') else None,
    get_new_value=lambda *args, **kwargs: args[0].model_dump() if args else None
)
async def create_task(
    request: Request,
    task: TaskCreate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> SuccessTaskCreateResponse:
    """
    Crea una nueva tarea de práctica cultural en el sistema.

    Parameters:
        task (TaskCreate): Datos de la tarea a crear.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que la tarea fue creada exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante la creación de la tarea.
    """
    create_task_use_case = CreateTaskUseCase(db)
    try:
        return create_task_use_case.create_task(task, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al crear la tarea: {str(e)}"
        ) from e

@router.post("/assignment/create", response_model=MultipleResponse, 
             responses={
                 200: {"description": "Todas las tareas asignadas exitosamente"},
                 207: {"description": "Algunas tareas asignadas, otras fallaron"},
                 400: {"description": "No se pudo asignar ninguna tarea"}
             })
@log_activity(
    action_type=LogActionType.ASSIGN_TASK,
    table_name="asignacion",
    severity=LogSeverity.INFO,
    description="Asignación de tarea de labor cultural a trabajadores con fecha y detalles",
    get_record_id=lambda *args, **kwargs: kwargs.get('result').task_id if kwargs.get('result') else None,
    get_new_value=lambda *args, **kwargs: args[0].model_dump() if args else None
)
async def create_assignment(
    request: Request,
    assignment: AssignmentCreate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> JSONResponse:
    """
    Crea una nueva asignación de práctica cultural en el sistema.

    Parameters:
        assignment (AssignmentCreate): Datos de la asignación a crear.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que la asignación fue creada exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante la creación de la asignación.
    """
    assign_task_use_case = AssignTaskUseCase(db)
    try:
        response = assign_task_use_case.create_assignment(assignment, current_user)
        return JSONResponse(content=response.model_dump(), status_code=response.status_code)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al asignar la tarea: {str(e)}"
        ) from e

@router.get("/farm/{farm_id}/user/{user_id}/tasks/list", response_model=PaginatedTaskListResponse, status_code=status.HTTP_200_OK)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="tarea_labor_cultural",
    severity=LogSeverity.INFO,
    description="Consulta de listado paginado de tareas por usuario y finca con estados y detalles"
)
async def list_tasks_by_user_and_farm(
    request: Request,
    farm_id: int,
    user_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> PaginatedTaskListResponse:
    """
    Lista todas las tareas asignadas a un usuario específico.

    Parameters:
        user_id (int): ID del usuario.
        page (int): Número de página.
        per_page (int): Elementos por página.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        PaginatedTaskListResponse: Una lista paginada de tareas.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de la lista de tareas.
    """
    list_tasks_by_user_and_farm_use_case = ListTasksByUserAndFarmUseCase(db)
    try:
        return list_tasks_by_user_and_farm_use_case.list_tasks_by_user_and_farm(farm_id, user_id, page, per_page, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar las tareas: {str(e)}"
        ) from e
        
@router.get("/farm/{farm_id}/tasks/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="tarea_labor_cultural",
    severity=LogSeverity.INFO,
    description="Consulta detallada de tarea específica con estado, asignaciones y datos relacionados",
    get_record_id=lambda *args, **kwargs: int(kwargs.get('task_id')) if kwargs.get('task_id') else None
)
async def get_task_by_id(
    request: Request,
    farm_id: int,
    task_id: int,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> TaskResponse:
    """
    Obtiene una tarea específica por su ID.

    Parameters:
        farm_id (int): ID de la finca.
        task_id (int): ID de la tarea.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        TaskResponse: Detalles de la tarea solicitada.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de la tarea.
    """
    get_task_by_id_use_case = GetTaskByIdUseCase(db)
    try:
        return get_task_by_id_use_case.get_task_by_id(farm_id, task_id, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener la tarea: {str(e)}"
        ) from e

@router.get("/tasks/states", response_model=TaskStateListResponse, status_code=status.HTTP_200_OK)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="estado_tarea_labor_cultural",
    severity=LogSeverity.INFO,
    description="Consulta del catálogo de estados disponibles para tareas de labor cultural"
)
async def list_task_states(
    request: Request,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> TaskStateListResponse:
    """
    Lista todos los estados de las tareas de prácticas culturales.

    Parameters:
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        List[TaskStateResponse]: Una lista de estados de tareas.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de los estados de las tareas.
    """
    list_task_states_use_case = ListTaskStatesUseCase(db)
    try:
        return list_task_states_use_case.list_task_states(current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar los estados de las tareas: {str(e)}"
        ) from e

@router.put(
    "/tasks/{task_id}/states/{state_id}", 
    response_model=SuccessResponse, 
    status_code=status.HTTP_200_OK
)
@log_activity(
    action_type=LogActionType.CHANGE_STATUS,
    table_name="tarea_labor_cultural",
    severity=LogSeverity.INFO,
    description="Actualización de estado de tarea cultural con registro de estado anterior y nuevo",
    get_record_id=lambda *args, **kwargs: int(kwargs.get('task_id')),
    get_old_value=lambda *args, **kwargs: {
        "estado_id": kwargs.get('task').estado_id
    } if kwargs.get('task') else None,
    get_new_value=lambda *args, **kwargs: {
        "estado_id": int(kwargs.get('state_id'))
    } if kwargs.get('state_id') else None
)
async def change_task_state(
    request: Request,
    task_id: int = Path(..., description="ID de la tarea", ge=1),
    state_id: Union[int, str] = Path(..., description="ID del estado o comando ('in_progress'/'done')"),
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> SuccessResponse:
    """
    Cambia el estado de una tarea de labor cultural.

    Parameters:
        task_id (int): ID de la tarea a cambiar el estado.
        state_id (Union[int, str]): ID del estado o comando ('in_progress', 'done').
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que el estado de la tarea fue cambiado exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante el cambio de estado de la tarea.
    """
    change_task_state_use_case = ChangeTaskStateUseCase(db)
    try:
        return change_task_state_use_case.change_task_state(task_id, state_id, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al cambiar de estado la tarea: {str(e)}"
        ) from e

@router.get("/tasks/types", response_model=TaskTypeListResponse, status_code=status.HTTP_200_OK)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="tipo_labor_cultural",
    severity=LogSeverity.INFO,
    description="Consulta del catálogo completo de tipos de labores culturales disponibles"
)
async def list_task_types(
    request: Request,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> TaskTypeListResponse:
    """
    Lista todos los tipos de labor cultural disponibles.

    Parameters:
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        TaskTypeListResponse: Una lista de tipos de labor cultural.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de los tipos de labor cultural.
    """
    list_task_types_use_case = ListTaskTypesUseCase(db)
    try:
        return list_task_types_use_case.list_task_types(current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar los tipos de labor cultural: {str(e)}"
        ) from e

@router.get("/tasks/types/{nivel}", response_model=TaskTypeListResponse)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="tipo_labor_cultural",
    severity=LogSeverity.INFO,
    description="Consulta de tipos de labor cultural filtrados por nivel LOTE o CULTIVO"
)
async def list_task_types_by_level(
    request: Request,
    nivel: NivelLaborCultural,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> TaskTypeListResponse:
    """Lista los tipos de labor cultural filtrados por nivel.

    Args:
        nivel (NivelLaborCultural): Nivel de labor cultural (LOTE o CULTIVO).
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        TaskTypeListResponse: Lista de tipos de labor cultural del nivel especificado.
    """
    list_task_types_by_level_use_case = ListTaskTypesByLevelUseCase(db)
    try:
        return list_task_types_by_level_use_case.list_task_types_by_level(nivel, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar los tipos de labor cultural: {str(e)}"
        ) from e

@router.get("/farms/{farm_id}/worker/tasks", response_model=PaginatedTaskListResponse, status_code=status.HTTP_200_OK)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="tarea_labor_cultural",
    severity=LogSeverity.INFO,
    description="Consulta de tareas asignadas al trabajador actual en finca específica",
    get_record_id=lambda *args, **kwargs: kwargs.get('current_user').id if kwargs.get('current_user') else None
)
async def list_worker_tasks(
    request: Request,
    farm_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> PaginatedTaskListResponse:
    """
    Lista todas las tareas asignadas al trabajador actual en una finca específica.

    Parameters:
        farm_id (int): ID de la finca.
        page (int): Número de página.
        per_page (int): Elementos por página.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado (trabajador).

    Returns:
        PaginatedTaskListResponse: Una lista paginada de tareas asignadas al trabajador.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de la lista de tareas.
    """
    list_worker_tasks_use_case = ListWorkerTasksUseCase(db)
    try:
        return list_worker_tasks_use_case.list_worker_tasks(farm_id, page, per_page, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar las tareas del trabajador: {str(e)}"
        ) from e

@router.get("/farms/{farm_id}/plots/{plot_id}/tasks", response_model=PaginatedTaskListResponse, status_code=status.HTTP_200_OK)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="tarea_labor_cultural",
    severity=LogSeverity.INFO,
    description="Consulta de tareas asociadas a lote específico con estados y detalles"
)
async def list_tasks_by_plot(
    request: Request,
    farm_id: int,
    plot_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> PaginatedTaskListResponse:
    """
    Lista todas las tareas asignadas a un lote específico.

    Parameters:
        farm_id (int): ID de la finca.
        plot_id (int): ID del lote.
        page (int): Número de página.
        per_page (int): Elementos por página.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        PaginatedTaskListResponse: Una lista paginada de tareas asignadas al lote.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de la lista de tareas.
    """
    list_tasks_by_plot_use_case = ListTasksByPlotUseCase(db)
    try:
        return list_tasks_by_plot_use_case.list_tasks_by_plot(farm_id, plot_id, page, per_page, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar las tareas del lote: {str(e)}"
        ) from e