"""
Este módulo define las rutas de la API para la gestión de costos.

Incluye endpoints para la creación de costos de tareas y asignaciones, así como para listar categorías de insumos y insumos agrícolas.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.costs.application.list_agricultural_machinery_use_case import ListAgriculturalMachineryUseCase
from app.costs.domain.schemas import AgriculturalMachineryListResponse, TaskCostsCreate, CostRegistrationResponse, AgriculturalInputCategoryListResponse, AgriculturalInputListResponse, MachineryTypeListResponse
from app.infrastructure.common.common_exceptions import DomainException
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.user.domain.schemas import UserInDB
from app.costs.application.register_task_costs_use_case import RegisterTaskCostsUseCase
from app.costs.application.list_input_categories_use_case import ListInputCategoriesUseCase
from app.costs.application.list_agricultural_inputs_use_case import ListAgriculturalInputsUseCase
from app.costs.application.list_machinery_types_use_case import ListMachineryTypesUseCase
from app.logs.application.services.log_service import LogActionType
from app.logs.application.decorators.log_decorator import log_activity

router = APIRouter(tags=["costs"])

@router.post("/farms/{farm_id}/tasks/{task_id}/costs", 
            response_model=CostRegistrationResponse, 
            status_code=status.HTTP_201_CREATED)
@log_activity(
    action_type=LogActionType.REGISTER_COSTS,
    table_name="costo_mano_obra",
    description=lambda *args, **kwargs: f"Registro de costos para tarea {kwargs.get('task_id')} en finca {kwargs.get('farm_id')}: mano de obra, insumos y maquinaria"
)
async def register_task_costs(
    farm_id: int,
    task_id: int,
    costs: TaskCostsCreate,
    request: Request,
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

@router.get("/input-categories", response_model=AgriculturalInputCategoryListResponse)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="categoria_insumo_agricola",
    description="Consulta del catálogo de categorías de insumos agrícolas disponibles"
)
async def list_input_categories(
    request: Request,
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

@router.get("/agricultural-inputs", response_model=AgriculturalInputListResponse)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="insumo_agricola",
    description="Consulta del catálogo de insumos agrícolas con sus especificaciones técnicas"
)
async def list_agricultural_inputs(
    request: Request,
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

@router.get("/machinery-types", response_model=MachineryTypeListResponse)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="tipo_maquinaria_agricola",
    description="Consulta del catálogo de tipos de maquinaria agrícola disponibles"
)
async def list_machinery_types(
    request: Request,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> MachineryTypeListResponse:
    """Lista todos los tipos de maquinaria agrícola.

    Args:
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        MachineryTypeListResponse: Lista de tipos de maquinaria.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de los tipos de maquinaria.
    """
    list_machinery_types_use_case = ListMachineryTypesUseCase(db)
    try:
        return list_machinery_types_use_case.list_machinery_types(current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar los tipos de maquinaria: {str(e)}"
        ) from e

@router.get("/agricultural-machinery", response_model=AgriculturalMachineryListResponse)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="maquinaria_agricola",
    description="Consulta del inventario de maquinaria agrícola con sus especificaciones técnicas"
)
async def list_agricultural_machinery(
    request: Request,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> AgriculturalMachineryListResponse:
    """Lista toda la maquinaria agrícola.

    Args:
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        AgriculturalMachineryListResponse: Lista de maquinaria agrícola.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de la maquinaria.
    """
    list_machinery_use_case = ListAgriculturalMachineryUseCase(db)
    try:
        return list_machinery_use_case.list_machinery(current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar la maquinaria agrícola: {str(e)}"
        ) from e