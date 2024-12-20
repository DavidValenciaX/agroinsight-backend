"""
Este módulo define las rutas de la API para la gestión de fincas.

Incluye endpoints para la creación de fincas, asignación de usuarios,
listado de fincas y usuarios de una finca específica.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.farm.application.list_farm_users_use_case import ListFarmUsersUseCase
from app.farm.application.list_worker_farms_use_case import ListWorkerFarmsUseCase
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.farm.domain.schemas import FarmCreate, PaginatedFarmListResponse, PaginatedFarmUserListResponse, FarmUserAssignmentByEmail, PaginatedWorkerFarmListResponse, FarmListResponse, FarmTasksStatsResponse, FarmRankingType, FarmRankingListResponse
from app.farm.application.create_farm_use_case import CreateFarmUseCase
from app.farm.application.list_farms_use_case import ListFarmsUseCase
from app.farm.application.assign_users_to_farm_use_case import AssignUsersToFarmUseCase
from app.infrastructure.common.response_models import MultipleResponse, SuccessResponse
from app.farm.application.get_user_by_id_use_case import AdminGetUserByIdUseCase
from app.logs.application.services.log_service import LogActionType
from app.user.domain.schemas import UserForFarmResponse, UserInDB
from app.infrastructure.common.common_exceptions import DomainException, UserStateException
from app.farm.application.list_all_farms_use_case import ListAllFarmsUseCase
from app.logs.application.decorators.log_decorator import log_activity
from app.farm.application.get_farm_tasks_stats_use_case import GetFarmTasksStatsUseCase
from datetime import date
from typing import Optional
from app.farm.application.get_farm_ranking_use_case import GetFarmRankingUseCase

router = APIRouter(prefix="/farm", tags=["farm"])

@router.post("/create", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
@log_activity(
    action_type=LogActionType.REGISTER_FARM,
    table_name="finca",
    description="Creación de nueva finca con información básica y asignación automática del usuario creador como administrador",
    get_record_id=lambda *args, **kwargs: args[0].id if args and hasattr(args[0], 'id') else None,
    get_new_value=lambda *args, **kwargs: kwargs.get('farm').to_log_dict() if 'farm' in kwargs else None
)
async def create_farm(
    request: Request,
    farm: FarmCreate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> SuccessResponse:
    """
    Crea una nueva finca en el sistema para un usuario específico.

    Parameters:
        farm (FarmCreate): Datos de la finca a crear.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que la finca fue creada exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante la creación de la finca.
    """
    crear_farm_use_case = CreateFarmUseCase(db)
    try:
        return crear_farm_use_case.create_farm(farm, current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al crear la finca: {str(e)}"
        )
        
@router.get("/list", response_model=PaginatedFarmListResponse, status_code=status.HTTP_200_OK)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="finca",
    description=lambda *args, **kwargs: f"Consulta de listado paginado de fincas donde el usuario es administrador. Página {kwargs.get('page')}, elementos por página: {kwargs.get('per_page')}"
)
async def list_farms(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> PaginatedFarmListResponse:
    """
    Lista todas las fincas en el sistema para un usuario específico.

    Parameters:
        page (int): Número de página.
        per_page (int): Elementos por página.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        PaginatedFarmListResponse: Una lista paginada de fincas.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de la lista de fincas.
    """
    list_farms_use_case = ListFarmsUseCase(db)
    try:
        return list_farms_use_case.list_farms(current_user, page, per_page)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar las fincas: {str(e)}"
        )
        
@router.post("/assign-users-by-email", 
             response_model=MultipleResponse,
             responses={
                 200: {"description": "Todos los usuarios asignados exitosamente"},
                 207: {"description": "Algunos usuarios asignados, otros fallaron"},
                 400: {"description": "No se pudo asignar ningún usuario"}
             }
)
@log_activity(
    action_type=LogActionType.ASSIGN_USER_TO_FARM,
    table_name="usuario_finca_rol",
    description="Asignación masiva de usuarios a finca por email",
    get_record_id=lambda *args, **kwargs: kwargs.get('assignment_data').farm_id if 'assignment_data' in kwargs else None,
    get_new_value=lambda *args, **kwargs: kwargs.get('assignment_data').model_dump() if 'assignment_data' in kwargs else None
)
async def assign_users_to_farm_by_email(
    request: Request,
    assignment_data: FarmUserAssignmentByEmail,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    assign_users_use_case = AssignUsersToFarmUseCase(db)
    try:
        response = assign_users_use_case.assign_users_by_emails(assignment_data, current_user)
        return JSONResponse(content=response.model_dump(), status_code=response.status_code)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al asignar usuarios a una finca: {str(e)}"
        )

        
@router.get("/{farm_id}/users", response_model=PaginatedFarmUserListResponse, status_code=status.HTTP_200_OK)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="usuario_finca_rol",
    description=lambda *args, **kwargs: f"Consulta de usuarios asignados a la finca {kwargs.get('farm_id')} con sus roles correspondientes"
)
async def list_farm_users(
    request: Request,
    farm_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(getDb)
):
    """
    Lista los usuarios de una finca específica.

    Parameters:
        farm_id (int): ID de la finca.
        page (int): Número de página.
        per_page (int): Elementos por página.
        current_user (User): Usuario actual autenticado.
        db (Session): Sesión de base de datos.

    Returns:
        PaginatedFarmUserListResponse: Una lista paginada de usuarios de la finca.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de la lista de usuarios.
    """
    
    use_case = ListFarmUsersUseCase(db)
    try:
        return use_case.list_farm_users(farm_id, current_user, page, per_page)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error al listar los usuarios de una finca: {str(e)}"
        )
        
@router.get("/{farm_id}/user/{user_id}", response_model=UserForFarmResponse, status_code=status.HTTP_200_OK)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="usuario",
    description=lambda *args, **kwargs: f"Consulta detallada de información y roles del usuario {kwargs.get('user_id')} en la finca {kwargs.get('farm_id')}"
)
async def get_user_by_id(
    request: Request,
    farm_id: int,
    user_id: int,
    db: Session = Depends(getDb),
    current_user=Depends(get_current_user)
):
    """
    Obtiene la información de un usuario por su ID y verifica roles en una finca específica.

    Parameters:
        farm_id (int): ID de la finca para verificar roles.
        user_id (int): ID del usuario a obtener.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        UserForFarmResponse: Un objeto UserForFarmResponse con la información del usuario.

    Raises:
        HTTPException: Si ocurre un error durante la obtención del usuario.
    """
    get_user_by_id_use_case = AdminGetUserByIdUseCase(db)
    try:
        return get_user_by_id_use_case.admin_get_user_by_id(user_id, farm_id, current_user)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener el usuario: {str(e)}"
        )

@router.get("/worker/farms", response_model=PaginatedWorkerFarmListResponse, status_code=status.HTTP_200_OK)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="finca",
    description=lambda *args, **kwargs: f"Consulta de listado paginado de fincas donde el usuario actual tiene rol de trabajador. Página {kwargs.get('page')}, elementos por página: {kwargs.get('per_page')}"
)
async def list_worker_farms(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> PaginatedWorkerFarmListResponse:
    """
    Lista todas las fincas donde el usuario actual es trabajador.

    Parameters:
        page (int): Número de página.
        per_page (int): Elementos por página.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        PaginatedWorkerFarmListResponse: Una lista paginada de fincas.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de la lista de fincas.
    """
    list_worker_farms_use_case = ListWorkerFarmsUseCase(db)
    try:
        return list_worker_farms_use_case.list_worker_farms(current_user, page, per_page)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar las fincas: {str(e)}"
        )

@router.get("/list/all", response_model=FarmListResponse, status_code=status.HTTP_200_OK)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="finca",
    description="Consulta de listado completo (sin paginación) de fincas donde el usuario es administrador"
)
async def list_all_farms(
    request: Request,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> FarmListResponse:
    """
    Lista todas las fincas en el sistema para un usuario específico sin paginación.

    Parameters:
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        FarmListResponse: Una lista completa de fincas.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de la lista de fincas.
    """
    list_all_farms_use_case = ListAllFarmsUseCase(db)
    try:
        return list_all_farms_use_case.list_all_farms(current_user)
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar las fincas: {str(e)}"
        )

@router.get("/{farm_id}/tasks/stats", response_model=FarmTasksStatsResponse)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="tarea_labor_cultural",
    description="Consulta de estadísticas de tareas de la finca"
)
async def get_farm_tasks_stats(
    request: Request,
    farm_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> FarmTasksStatsResponse:
    """
    Obtiene estadísticas de las tareas de una finca específica.

    Parameters:
        farm_id (int): ID de la finca.
        start_date (Optional[date]): Fecha inicial del rango de filtrado.
        end_date (Optional[date]): Fecha final del rango de filtrado.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        FarmTasksStatsResponse: Estadísticas de tareas de la finca.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de las estadísticas.
    """
    get_farm_tasks_stats_use_case = GetFarmTasksStatsUseCase(db)
    try:
        return get_farm_tasks_stats_use_case.get_farm_tasks_stats(
            farm_id, 
            current_user,
            start_date,
            end_date
        )
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener las estadísticas: {str(e)}"
        )

@router.get("/ranking", response_model=FarmRankingListResponse)
@log_activity(
    action_type=LogActionType.VIEW,
    table_name="finca",
    description="Consulta de ranking de fincas por ganancias o producción"
)
async def get_farm_ranking(
    request: Request,
    ranking_type: FarmRankingType,
    limit: int = Query(10, ge=1, le=100, description="Cantidad máxima de fincas"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
) -> FarmRankingListResponse:
    """
    Obtiene un ranking de las fincas del usuario según ganancias o producción.

    Parameters:
        ranking_type (FarmRankingType): Tipo de ranking (PROFIT/PRODUCTION)
        limit (int): Cantidad máxima de fincas a retornar
        start_date (Optional[date]): Fecha inicial del período
        end_date (Optional[date]): Fecha final del período
        db (Session): Sesión de base de datos
        current_user (UserInDB): Usuario actual autenticado

    Returns:
        FarmRankingListResponse: Ranking de fincas según el criterio especificado

    Raises:
        HTTPException: Si ocurre un error durante la obtención del ranking
    """
    get_farm_ranking_use_case = GetFarmRankingUseCase(db)
    try:
        return get_farm_ranking_use_case.get_farm_ranking(
            current_user,
            ranking_type,
            limit,
            start_date,
            end_date
        )
    except DomainException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener el ranking de fincas: {str(e)}"
        )