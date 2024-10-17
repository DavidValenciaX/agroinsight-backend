"""
Este módulo define las rutas de la API para la gestión de prácticas culturales.

Incluye endpoints para la creación de tareas y asignaciones, así como para listar asignaciones.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.cultural_practices.domain.schemas import AssignmentCreate, TaskCreate, PaginatedTaskListResponse, SuccessTaskCreateResponse, TaskStateListResponse, TaskStateResponse
from app.cultural_practices.application.create_assignment_use_case import CreateAssignmentUseCase
from app.cultural_practices.application.create_task_use_case import CreateTaskUseCase
from app.infrastructure.common.common_exceptions import DomainException
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.infrastructure.common.response_models import MultipleResponse, SuccessResponse
from app.user.domain.schemas import UserInDB
from app.cultural_practices.application.list_tasks_by_user_and_farm_use_case import ListTasksByUserAndFarmUseCase
from app.cultural_practices.application.change_task_state_use_case import ChangeTaskStateUseCase
from app.cultural_practices.application.list_task_states_use_case import ListTaskStatesUseCase

router = APIRouter(tags=["cultural practices"])

@router.post("/task/create", response_model=SuccessTaskCreateResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task: TaskCreate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
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
        )

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
):
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
    create_assignment_use_case = CreateAssignmentUseCase(db)
    try:
        response = create_assignment_use_case.create_assignment(assignment, current_user)
        return JSONResponse(content=response.model_dump(), status_code=response.status_code)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al asignar la tarea: {str(e)}"
        )

@router.get("/farm/{farm_id}/user/{user_id}/tasks/list", response_model=PaginatedTaskListResponse, status_code=status.HTTP_200_OK)
def list_tasks_by_user_and_farm(
    farm_id: int,
    user_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
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
        )
        
@router.get("/tasks/states", response_model=TaskStateListResponse, status_code=status.HTTP_200_OK)
def list_task_states(
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
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
        )

@router.put("/tasks/{task_id}/states/{state_id}", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def change_task_state(
    task_id: int,
    state_id: int,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Cambia el estado de una tarea de labor cultural.

    Parameters:
        task_id (int): ID de la tarea a cambiar el estado.
        state_id (int): ID del estado al que se cambiará la tarea.
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
        )