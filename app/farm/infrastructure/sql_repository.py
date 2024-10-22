from sqlalchemy.orm import Session
from app.farm.domain.schemas import FarmCreate
from app.farm.infrastructure.orm_models import Farm
from typing import Optional, List, Tuple
from typing import List
from fastapi import status
from app.infrastructure.common.common_exceptions import DomainException
from app.user.infrastructure.orm_models import Role, User, UserFarmRole
from app.user.infrastructure.sql_repository import UserRepository
from app.user.application.services.user_service import UserService

class FarmRepository:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.user_service = UserService(db)
        
    def create_farm(self, farm_data: FarmCreate) -> Optional[Farm]:
        try:
            # Crear el modelo ORM
            new_farm = Farm(
                nombre=farm_data.nombre,
                ubicacion=farm_data.ubicacion,
                area_total=farm_data.area_total,
                unidad_area_id=farm_data.unidad_area_id
            )
        
            self.db.add(new_farm)
            self.db.flush()
            self.db.commit()
            self.db.refresh(new_farm)
            return new_farm
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear la finca: {e}")
            return None
        
    def list_farms_by_role_paginated(self, user_id: int, rol_id: int, page: int, per_page: int) -> Tuple[int, List[Farm]]:
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
    
    def get_farm_by_name(self, farm_name: str) -> Optional[Farm]:
        return self.db.query(Farm).filter(Farm.nombre == farm_name).first()
    
    def list_farm_users_paginated(self, farm_id: int, page: int, per_page: int):
        offset = (page - 1) * per_page
        query = self.db.query(User).join(UserFarmRole).filter(UserFarmRole.finca_id == farm_id)
        total = query.count()
        users = query.offset(offset).limit(per_page).all()
        return total, users
        
    def get_user_farm_role(self, user_id: int, farm_id: int, role_id: int) -> Optional[UserFarmRole]:
        return self.db.query(UserFarmRole).filter(
            UserFarmRole.usuario_id == user_id,
            UserFarmRole.finca_id == farm_id,
            UserFarmRole.rol_id == role_id
        ).first()

    def add_user_to_farm_with_role(self, user_id: int, farm_id: int, role_id: int):
        try:
            user_farm = UserFarmRole(usuario_id=user_id, finca_id=farm_id, rol_id=role_id)
            self.db.add(user_farm)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear al asignar rol a usuario en finca: {e}")
            return False