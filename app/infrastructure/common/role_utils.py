from sqlalchemy.orm import Session
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException  # Ensure this import is correct
from fastapi import status

ADMIN_ROLE_NAME = "Administrador de Finca"
WORKER_ROLE_NAME = "Trabajador agrícola"

def get_admin_role(db: Session):
    user_repository = UserRepository(db)
    try:
        return user_repository.get_role_by_name(ADMIN_ROLE_NAME)
    except Exception as e:
        raise DomainException(message = f"Error retrieving admin role: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_worker_role(db: Session):
    user_repository = UserRepository(db)
    try:
        return user_repository.get_role_by_name(WORKER_ROLE_NAME)
    except Exception as e:
        raise DomainException(message = f"Error retrieving worker role: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
