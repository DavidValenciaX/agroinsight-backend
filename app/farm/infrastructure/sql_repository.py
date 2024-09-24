from sqlalchemy.orm import Session
from app.farm.infrastructure.orm_models import Finca, UnidadMedida, UsuarioFinca
from app.farm.domain.schemas import FincaCreate
from typing import Optional

class FincaRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_finca(self, finca_data: FincaCreate, user_id: int) -> Optional[Finca]:
        try:
            # Crear la finca
            new_finca = Finca(
                nombre=finca_data.nombre,
                ubicacion=finca_data.ubicacion,
                area_total=finca_data.area_total,
                unidad_area_id=finca_data.unidad_area_id,
                latitud=finca_data.latitud,
                longitud=finca_data.longitud
            )
            self.db.add(new_finca)
            self.db.flush()  # Para obtener el ID de la finca recién creada

            # Crear la relación usuario-finca
            usuario_finca = UsuarioFinca(usuario_id=user_id, finca_id=new_finca.id)
            self.db.add(usuario_finca)

            self.db.commit()
            self.db.refresh(new_finca)
            return new_finca
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear la finca: {e}")
            return None

    def get_unidad_medida_by_id(self, unidad_id: int) -> Optional[UnidadMedida]:
        return self.db.query(UnidadMedida).filter(UnidadMedida.id == unidad_id).first()

    # Agregar más métodos según sea necesario