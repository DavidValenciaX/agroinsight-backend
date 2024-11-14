"""
Este módulo define las rutas de la API para la gestión de prácticas culturales.

Incluye endpoints para la creación de tareas y asignaciones, así como para listar asignaciones.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.cultural_practices.application.get_task_by_id_use_case import GetTaskByIdUseCase
from app.cultural_practices.domain.schemas import AssignmentCreate, TaskCreate, PaginatedTaskListResponse, SuccessTaskCreateResponse, TaskResponse, TaskStateListResponse, TaskTypeListResponse, TaskCostsCreate, CostRegistrationResponse, AgriculturalInputCategoryListResponse, AgriculturalInputListResponse
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
from app.cultural_practices.application.register_task_costs_use_case import RegisterTaskCostsUseCase
from app.cultural_practices.application.list_input_categories_use_case import ListInputCategoriesUseCase
from app.cultural_practices.application.list_agricultural_inputs_use_case import ListAgriculturalInputsUseCase

router = APIRouter(tags=["cultural practices"])

@router.post("/task/create", response_model=SuccessTaskCreateResponse, status_code=status.HTTP_201_CREATED)
def create_task(
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
             }
)
def create_assignment(
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
def list_tasks_by_user_and_farm(
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
def get_task_by_id(
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
def list_task_states(
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
def change_task_state(
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
def list_task_types(
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

@router.get("/farms/{farm_id}/worker/tasks", response_model=PaginatedTaskListResponse, status_code=status.HTTP_200_OK)
def list_worker_tasks(
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
def list_tasks_by_plot(
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

@router.post("/farms/{farm_id}/tasks/{task_id}/costs", 
            response_model=CostRegistrationResponse, 
            status_code=status.HTTP_201_CREATED)
def register_task_costs(
    farm_id: int,
    task_id: int,
    costs: TaskCostsCreate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> CostRegistrationResponse:
    """
    Registra los costos asociados a una tarea cultural.

    Parameters:
        farm_id (int): ID de la finca.
        task_id (int): ID de la tarea.
        costs (TaskCostsCreate): Datos de los costos a registrar.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        CostRegistrationResponse: Respuesta indicando el resultado del registro de costos.

    Raises:
        HTTPException: Si ocurre un error durante el registro de los costos.
    """
    register_task_costs_use_case = RegisterTaskCostsUseCase(db)
    try:
        return register_task_costs_use_case.register_costs(task_id, farm_id, costs, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al registrar los costos: {str(e)}"
        ) from e

@router.get("/input-categories", response_model=AgriculturalInputCategoryListResponse, status_code=status.HTTP_200_OK)
def list_input_categories(
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> AgriculturalInputCategoryListResponse:
    """Lista todas las categorías de insumos agrícolas.

    Args:
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        AgriculturalInputCategoryListResponse: Lista de categorías de insumos.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de las categorías.
    """
    list_categories_use_case = ListInputCategoriesUseCase(db)
    try:
        return list_categories_use_case.list_categories(current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar las categorías de insumos: {str(e)}"
        ) from e

@router.get("/agricultural-inputs", response_model=AgriculturalInputListResponse, status_code=status.HTTP_200_OK)
def list_agricultural_inputs(
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> AgriculturalInputListResponse:
    """Lista todos los insumos agrícolas.

    Args:
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        AgriculturalInputListResponse: Lista de insumos agrícolas.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de los insumos.
    """
    list_inputs_use_case = ListAgriculturalInputsUseCase(db)
    try:
        return list_inputs_use_case.list_inputs(current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar los insumos agrícolas: {str(e)}"
        ) from e
