from sqlalchemy.orm import Session
from app.farm.infrastructure.orm_models import Finca, UnidadMedida, UsuarioFinca
from app.farm.domain.schemas import FarmCreate
from typing import Optional, List

class FarmRepository:
    def __init__(self, db: Session):
        self.db = db

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

            # Crear la relación usuario-finca
            user_farm = UsuarioFinca(usuario_id=user_id, finca_id=new_farm.id)
            self.db.add(user_farm)

            self.db.commit()
            self.db.refresh(new_farm)
            return new_farm
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear la finca: {e}")
            return None

    def get_unidad_medida_by_id(self, unidad_id: int) -> Optional[UnidadMedida]:
        return self.db.query(UnidadMedida).filter(UnidadMedida.id == unidad_id).first()
    
    def list_farms(self, user_id: int) -> List[Finca]:
            return self.db.query(Finca).join(UsuarioFinca).filter(UsuarioFinca.usuario_id == user_id).all()
        
    def farm_exists_for_user(self, user_id: int, farm_name: str) -> bool:
        """
        Verifica si ya existe una finca con el mismo nombre para el usuario dado.
        """
        return self.db.query(Finca).join(UsuarioFinca).filter(
            UsuarioFinca.usuario_id == user_id,
            Finca.nombre == farm_name
        ).first() is not None