"""
Este módulo define las rutas de la API para la gestión de costos.

Incluye endpoints para la creación de costos de tareas y asignaciones, así como para listar categorías de insumos y insumos agrícolas.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.costs.domain.schemas import TaskCostsCreate, CostRegistrationResponse, AgriculturalInputCategoryListResponse, AgriculturalInputListResponse
from app.infrastructure.common.common_exceptions import DomainException
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.user.domain.schemas import UserInDB
from app.costs.application.register_task_costs_use_case import RegisterTaskCostsUseCase
from app.costs.application.list_input_categories_use_case import ListInputCategoriesUseCase
from app.costs.application.list_agricultural_inputs_use_case import ListAgriculturalInputsUseCase

router = APIRouter(tags=["costs"])

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
