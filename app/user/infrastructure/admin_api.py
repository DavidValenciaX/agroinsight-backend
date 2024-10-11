from typing import List
from app.user.application.admin_use_cases.admin_deactivates_user_use_case import AdminDeactivatesUserUseCase
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserResponse, UserInDB
from app.infrastructure.common.common_exceptions import DomainException, UserStateException
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

admin_router = APIRouter(prefix="/user", tags=["admin"])
        
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