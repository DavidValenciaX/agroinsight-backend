"""
Este módulo define las rutas de la API para la gestión de prácticas culturales.

Incluye endpoints para la creación de tareas y asignaciones, así como para listar asignaciones.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.cultural_practices.application.list_assignments_use_case import ListAssignmentsUseCase
from app.cultural_practices.domain.schemas import AssignmentCreate, TareaLaborCulturalCreate
from app.cultural_practices.application.create_assignment_use_case import CreateAssignmentUseCase
from app.cultural_practices.domain.schemas import PaginatedAssignmentListResponse
from app.cultural_practices.application.create_task_use_case import CreateTaskUseCase
from app.infrastructure.common.common_exceptions import DomainException
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserInDB

router = APIRouter(prefix="/cultural_practices", tags=["cultural practices"])

@router.post("/create-task", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task: TareaLaborCulturalCreate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Crea una nueva tarea de práctica cultural en el sistema.

    Parameters:
        task (TareaLaborCulturalCreate): Datos de la tarea a crear.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que la tarea fue creada exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante la creación de la tarea.
    """
    create_task_use_case = CreateTaskUseCase(db)
    try:
        return create_task_use_case.execute(task, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al crear la tarea: {str(e)}"
        )

@router.post("/create-assignment", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
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
        return create_assignment_use_case.execute(assignment, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al asignar la tarea: {str(e)}"
        )
        
@router.get("/list-assignments/{user_id}", response_model=PaginatedAssignmentListResponse, status_code=status.HTTP_200_OK)
def list_assignments(
    user_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Lista todas las asignaciones de prácticas culturales para un usuario específico.

    Parameters:
        user_id (int): ID del usuario.
        page (int): Número de página.
        per_page (int): Elementos por página.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        PaginatedAssignmentListResponse: Una lista paginada de asignaciones.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de la lista de asignaciones.
    """
    list_assignments_use_case = ListAssignmentsUseCase(db)
    try:
        return list_assignments_use_case.execute(user_id, page, per_page, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar las asignaciones: {str(e)}"
        )