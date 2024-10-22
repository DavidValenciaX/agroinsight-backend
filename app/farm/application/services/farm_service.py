from typing import Optional
from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.infrastructure.common.common_exceptions import DomainException
from app.user.application.services.user_service import UserService
from app.user.infrastructure.orm_models import Role
from app.user.infrastructure.sql_repository import UserRepository
from fastapi import status

class FarmService:
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.user_service = UserService(db)
        self.farm_repository = FarmRepository(db)

    def user_is_farm_admin(self, user_id: int, farm_id: int) -> bool:
        admin_role = self.get_admin_role()
        return self.farm_repository.get_user_farm_role(user_id, farm_id, admin_role.id) is not None
    
    def user_is_farm_worker(self, user_id: int, farm_id: int) -> bool:
        worker_role = self.get_worker_role()
        return self.farm_repository.get_user_farm_role(user_id, farm_id, worker_role.id) is not None
    
    def get_admin_role(self) -> Optional[Role]:
        rol_administrador_finca = self.user_repository.get_role_by_name(self.user_service.ADMIN_ROLE_NAME)
        if not rol_administrador_finca:
            raise DomainException(
                message="No se pudo obtener el rol de Administrador de Finca.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return rol_administrador_finca
    
    def get_worker_role(self) -> Optional[Role]:
        rol_trabajador_agricola = self.user_repository.get_role_by_name(self.user_service.WORKER_ROLE_NAME) 
        if not rol_trabajador_agricola:
            raise DomainException(
                message="No se pudo asignar el rol de Trabajador Agrícola.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return rol_trabajador_agricola