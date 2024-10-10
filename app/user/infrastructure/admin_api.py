from typing import List
from app.user.application.admin_use_cases.admin_deactivates_user_use_case import AdminDeactivatesUserUseCase
from app.user.application.admin_use_cases.admin_updates_user_use_case import AdminUpdatesUserUseCase
from app.user.application.admin_use_cases.admin_creates_user_use_case import AdminCreatesUserUseCase
from app.user.application.admin_use_cases.admin_list_users_use_case import AdminListUsersUseCase
from app.user.application.admin_use_cases.admin_get_user_by_id_use_case import AdminGetUserByIdUseCase
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserCreateByAdmin, UserResponse, AdminUserUpdate, UserInDB
from app.infrastructure.common.common_exceptions import DomainException, UserStateException
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session


admin_router = APIRouter(prefix="/user", tags=["admin"])

@admin_router.post(
    "/admin/create", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED
)
def create_user_by_admin(
    user: UserCreateByAdmin,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Crea un nuevo usuario en el sistema por un administrador.

    Parameters:
        user (UserCreateByAdmin): Datos del usuario a crear.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que el usuario fue creado exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante la creación del usuario.
    """
    user_creation_by_admin_use_case = AdminCreatesUserUseCase(db)
    try:
        return user_creation_by_admin_use_case.admin_creates_user(user, current_user)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno en el registro de usuario por el administrador: {str(e)}"
        )
        
@admin_router.get("/list", response_model=List[UserResponse], status_code=status.HTTP_200_OK)
def list_users(db: Session = Depends(getDb), current_user=Depends(get_current_user)):
    """
    Lista todos los usuarios en el sistema.

    Parameters:
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        List[UserResponse]: Una lista de objetos UserResponse representando a los usuarios.

    Raises:
        HTTPException: Si ocurre un error durante la obtención de la lista de usuarios.
    """
    list_users_use_case = AdminListUsersUseCase(db)
    try:
        return list_users_use_case.admin_list_users(current_user)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al listar los usuarios: {str(e)}"
        )
        
@admin_router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_user_by_id(user_id: int, db: Session = Depends(getDb), current_user=Depends(get_current_user)):
    """
    Obtiene la información de un usuario por su ID.

    Parameters:
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
        return get_user_by_id_use_case.admin_get_user_by_id(user_id, current_user)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener el usuario: {str(e)}"
        )
        
@admin_router.put("/{user_id}/update", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def admin_update_user(
    user_id: int,
    user_update: AdminUserUpdate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Actualiza la información de un usuario por un administrador.

    Parameters:
        user_id (int): ID del usuario a actualizar.
        user_update (AdminUserUpdate): Datos de actualización del usuario.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que el usuario fue actualizado exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante la actualización del usuario.
    """
    update_user_use_case = AdminUpdatesUserUseCase(db)
    try:
        return update_user_use_case.admin_updates_user(user_id, user_update, current_user)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo actualizar la información del usuario: {str(e)}"
        )
        
@admin_router.delete("/{user_id}/deactivate", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def deactivate_user(
    user_id: int, 
    db: Session = Depends(getDb), 
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Desactiva un usuario en el sistema.

    Parameters:
        user_id (int): ID del usuario a desactivar.
        db (Session): Sesión de base de datos.
        current_user (UserInDB): Usuario actual autenticado.

    Returns:
        SuccessResponse: Un objeto SuccessResponse indicando que el usuario fue desactivado exitosamente.

    Raises:
        HTTPException: Si ocurre un error durante la desactivación del usuario.
    """
    deactivate_use_case = AdminDeactivatesUserUseCase(db)
    try:
        return deactivate_use_case.admin_deactivates_user(user_id, current_user)
    except (DomainException, UserStateException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo eliminar el usuario: {str(e)}"
        )