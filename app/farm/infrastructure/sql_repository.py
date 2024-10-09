from sqlalchemy.orm import Session
from app.farm.infrastructure.orm_models import Finca, UnidadMedida
from app.farm.domain.schemas import FarmCreate
from typing import Optional, List, Tuple
from app.farm.infrastructure.orm_models import Finca
from typing import List
from fastapi import status

from app.infrastructure.common.common_exceptions import DomainException
from app.user.infrastructure.orm_models import User, UsuarioFincaRol, UsuarioFincaRol
from app.user.infrastructure.sql_repository import UserRepository

class FarmRepository:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def create_farm(self, farm_data: FarmCreate, user_id: int) -> Optional[Finca]:
        try:
            # Crear la finca
            new_farm = Finca(
                nombre=farm_data.nombre,
                ubicacion=farm_data.ubicacion,
                area_total=farm_data.area_total,
                unidad_area_id=farm_data.unidad_area_id,
                latitud=farm_data.latitud,
                longitud=farm_data.longitud
            )
            self.db.add(new_farm)
            self.db.flush()  # Para obtener el ID de la finca recién creada
            
            # Obtener el rol de administrador de finca
            admin_role = self.user_repository.get_role_by_name("Administrador de Finca")
            if not admin_role:
                raise DomainException(
                    message="No se pudo encontrar el rol de 'Administrador de Finca'.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
            # Crear la relación usuario-finca
            user_farm = UsuarioFincaRol(usuario_id=user_id, finca_id=new_farm.id, rol_id=admin_role.id)
            self.db.add(user_farm)

            self.db.commit()
            self.db.refresh(new_farm)
            return new_farm
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear la finca: {e}")
            return None
    
    def list_farms(self, user_id: int) -> List[Finca]:
            return self.db.query(Finca).join(UsuarioFincaRol).filter(UsuarioFincaRol.usuario_id == user_id).all()
        
    def farm_exists_for_user(self, user_id: int, farm_name: str) -> bool:
        return self.db.query(Finca).join(UsuarioFincaRol).filter(
            UsuarioFincaRol.usuario_id == user_id,
            Finca.nombre == farm_name
        ).first() is not None
        
    def list_farms_paginated(self, user_id: int, page: int, per_page: int) -> Tuple[int, List[Finca]]:
        query = self.db.query(Finca).join(UsuarioFincaRol).filter(UsuarioFincaRol.usuario_id == user_id)
        
        total = query.count()
        farms = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return total, farms
    
    def assign_users_to_farm(self, farm_id: int, user_ids: List[int], role_id: int) -> List[int]:
        assigned_user_ids = []
        for user_id in user_ids:
            user_farm_role = UsuarioFincaRol(usuario_id=user_id, finca_id=farm_id, rol_id=role_id)
            self.db.merge(user_farm_role)
            assigned_user_ids.append(user_id)
        self.db.commit()
        return assigned_user_ids

    def get_farm_by_id(self, farm_id: int) -> Finca:
        return self.db.query(Finca).filter(Finca.id == farm_id).first()
    
    def list_farm_users_by_role_paginated(self, farm_id: int, role_id: int, page: int, per_page: int):
        offset = (page - 1) * per_page
        query = (
            self.db.query(User)
            .join(UsuarioFincaRol, UsuarioFincaRol.usuario_id == User.id)
            .filter(UsuarioFincaRol.finca_id == farm_id)
            .filter(UsuarioFincaRol.rol_id == role_id)
        )
        total = query.count()
        users = query.offset(offset).limit(per_page).all()
        return total, users
    
    def user_has_access_to_farm(self, user_id: int, farm_id: int) -> bool:
        return self.db.query(UsuarioFincaRol).filter(
            UsuarioFincaRol.usuario_id == user_id,
            UsuarioFincaRol.finca_id == farm_id
        ).first() is not None