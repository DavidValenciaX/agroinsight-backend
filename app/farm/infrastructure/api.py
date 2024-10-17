"""
Este módulo define las rutas de la API para la gestión de fincas.

Incluye endpoints para la creación de fincas, asignación de usuarios,
listado de fincas y usuarios de una finca específica.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.farm.application.list_farm_users_use_case import ListFarmUsersUseCase
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.farm.domain.schemas import FarmCreate, PaginatedFarmListResponse, PaginatedFarmUserListResponse, FarmUserAssignmentByEmail
from app.farm.application.create_farm_use_case import CreateFarmUseCase
from app.farm.application.list_farms_use_case import ListFarmsUseCase
from app.farm.application.assign_users_to_farm_use_case import AssignUsersToFarmUseCase
from app.infrastructure.common.response_models import MultipleResponse, SuccessResponse
from app.farm.application.get_user_by_id_use_case import AdminGetUserByIdUseCase
from app.user.domain.schemas import UserInDB, UserResponse
from app.infrastructure.common.common_exceptions import DomainException, UserStateException
from app.user.infrastructure.orm_models import User

router = APIRouter(prefix="/farm", tags=["farm"])

@router.post("/create", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def create_farm(
    farm: FarmCreate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
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
def list_farms(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
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
                 200: {"description": "Usuarios asignados exitosamente"},
                 207: {"description": "Algunos usuarios asignados, otros fallaron"},
                 400: {"description": "No se pudo asignar ningún usuario"}
             }
)
def assign_users_to_farm_by_email(
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
            detail=f"Error interno al asignar usuario a una finca: {str(e)}"
        )

        
@router.get("/{farm_id}/users", response_model=PaginatedFarmUserListResponse, status_code=status.HTTP_200_OK)
def list_farm_users(
    farm_id: int,
    page: Optional[int] = Query(1, ge=1),
    per_page: Optional[int] = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(getDb)
):
    """
    Lista los usuarios de una finca específica.

    Parameters:
        farm_id (int): ID de la finca.
        role_id (int): ID del rol a filtrar.
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
        
@router.get("/{farm_id}/user/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_user_by_id(
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
        UserResponse: Un objeto UserResponse con la información del usuario.

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
