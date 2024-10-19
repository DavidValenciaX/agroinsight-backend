from sqlalchemy.orm import Session
from app.farm.infrastructure.orm_models import Farm
from app.farm.domain.schemas import FarmCreate
from typing import Optional, List, Tuple
from typing import List
from fastapi import status
from app.infrastructure.common.common_exceptions import DomainException
from app.user.infrastructure.orm_models import Role, User, UserFarmRole
from app.user.infrastructure.sql_repository import UserRepository

# Constantes para roles
ADMIN_ROLE_NAME = "Administrador de Finca"
WORKER_ROLE_NAME = "Trabajador Agrícola"

class FarmRepository:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def create_farm(self, farm_data: FarmCreate, user_id: int) -> Optional[Farm]:
        try:
            # Crear la finca
            new_farm = Farm(
                nombre=farm_data.nombre,
                ubicacion=farm_data.ubicacion,
                area_total=farm_data.area_total,
                unidad_area_id=farm_data.unidad_area_id,
            )
            self.db.add(new_farm)
            self.db.flush()  # Para obtener el ID de la finca recién creada
            
            admin_role = self.get_admin_role()
            
            # Crear la relación usuario-finca
            self.assign_user_to_farm_with_role(user_id, new_farm.id, admin_role.id)

            self.db.commit()
            self.db.refresh(new_farm)
            return new_farm
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear la finca: {e}")
            return None
    
    def list_farms(self, user_id: int) -> List[Farm]:
            return self.db.query(Farm).join(UserFarmRole).filter(UserFarmRole.usuario_id == user_id).all()
        
    def farm_exists_for_user(self, user_id: int, farm_name: str) -> bool:
        return self.db.query(Farm).join(UserFarmRole).filter(
            UserFarmRole.usuario_id == user_id,
            Farm.nombre == farm_name
        ).first() is not None
        
    def list_farms_by_role_paginated(self, user_id: int, rol_id: int, page: int, per_page: int) -> Tuple[int, List[Farm]]:
        # Filtrar las fincas donde el usuario tiene el rol de "Administrador de Finca"
        query = self.db.query(Farm).join(UserFarmRole).filter(
            UserFarmRole.usuario_id == user_id,
            UserFarmRole.rol_id == rol_id
        )
        
        total = query.count()
        farms = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return total, farms
    
    def get_user_farm(self, user_id: int, farm_id: int) -> UserFarmRole:
        return self.db.query(UserFarmRole).filter(
            UserFarmRole.usuario_id == user_id,
            UserFarmRole.finca_id == farm_id
        ).first()

    def get_farm_by_id(self, farm_id: int) -> Optional[Farm]:
        return self.db.query(Farm).filter(Farm.id == farm_id).first()
    
    def list_farm_users_by_role_paginated(self, farm_id: int, role_id: int, page: int, per_page: int):
        offset = (page - 1) * per_page
        query = (
            self.db.query(User)
            .join(UserFarmRole, UserFarmRole.usuario_id == User.id)
            .filter(UserFarmRole.finca_id == farm_id)
            .filter(UserFarmRole.rol_id == role_id)
        )
        total = query.count()
        users = query.offset(offset).limit(per_page).all()
        return total, users
    
    def list_farm_users_paginated(self, farm_id: int, page: int, per_page: int):
        offset = (page - 1) * per_page
        query = self.db.query(User).join(UserFarmRole).filter(UserFarmRole.finca_id == farm_id)
        total = query.count()
        users = query.offset(offset).limit(per_page).all()
        return total, users
    
    def user_has_access_to_farm(self, user_id: int, farm_id: int) -> bool:
        return self.db.query(UserFarmRole).filter(
            UserFarmRole.usuario_id == user_id,
            UserFarmRole.finca_id == farm_id
        ).first() is not None
        
    def user_is_farm_admin(self, user_id: int, farm_id: int) -> bool:
        return self.db.query(UserFarmRole).filter(
            UserFarmRole.usuario_id == user_id,
            UserFarmRole.finca_id == farm_id,
            UserFarmRole.rol_id == self.get_admin_role().id
        ).first() is not None
    
    def user_is_farm_worker(self, user_id: int, farm_id: int) -> bool:
        return self.db.query(UserFarmRole).filter(
            UserFarmRole.usuario_id == user_id,
            UserFarmRole.finca_id == farm_id,
            UserFarmRole.rol_id == self.get_worker_role().id
        ).first() is not None
        
    def get_farms_by_user_role(self, user_id: int, role_id: int) -> List[int]:
        return [finca_id for finca_id, in self.db.query(UserFarmRole.finca_id).filter(
            UserFarmRole.usuario_id == user_id,
            UserFarmRole.rol_id == role_id
        ).all()]

    def assign_user_to_farm_with_role(self, user_id: int, farm_id: int, role_id: int):
        try:
            user_farm = UserFarmRole(usuario_id=user_id, finca_id=farm_id, rol_id=role_id)
            self.db.add(user_farm)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear al asignar rol a usuario en finca: {e}")
            raise DomainException(
                message="No se pudo asignar el rol al usuario en la finca.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_worker_role(self) -> Optional[Role]:
        rol_trabajador_agricola = self.user_repository.get_role_by_name(WORKER_ROLE_NAME) 
        if not rol_trabajador_agricola:
            raise DomainException(
                message="No se pudo asignar el rol de Trabajador Agrícola.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return rol_trabajador_agricola
    
    def get_admin_role(self) -> Optional[Role]:
        rol_administrador_finca = self.user_repository.get_role_by_name(ADMIN_ROLE_NAME)
        if not rol_administrador_finca:
            raise DomainException(
                message="No se pudo obtener el rol de Administrador de Finca.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return rol_administrador_finca