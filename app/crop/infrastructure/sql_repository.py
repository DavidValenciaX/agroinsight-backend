from typing import Optional, List
from sqlalchemy.orm import Session
from app.crop.infrastructure.orm_models import Crop, CropState, CornVariety
from app.crop.domain.schemas import CropCreate

class CropRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def create_crop(self, crop_data: CropCreate) -> Optional[Crop]:
        """
        Crea un nuevo cultivo en la base de datos.

        Args:
            crop_data (CropCreate): Datos del cultivo a crear.

        Returns:
            Optional[Crop]: El cultivo creado si tiene éxito, None en caso de error.
        """
        try:
            new_crop = Crop(
                lote_id=crop_data.lote_id,
                variedad_maiz_id=crop_data.variedad_maiz_id,
                fecha_siembra=crop_data.fecha_siembra,
                densidad_siembra=crop_data.densidad_siembra,
                densidad_siembra_unidad_id=crop_data.densidad_siembra_unidad_id,
                estado_id=crop_data.estado_id
            )
            self.db.add(new_crop)
            self.db.commit()
            self.db.refresh(new_crop)
            return new_crop
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear el cultivo: {e}")
            return None

    def get_corn_variety_by_id(self, variety_id: int) -> Optional[CornVariety]:
        """
        Obtiene una variedad de maíz por su ID.

        Args:
            variety_id (int): ID de la variedad de maíz.

        Returns:
            Optional[CornVariety]: La variedad de maíz si se encuentra, None en caso contrario.
        """
        return self.db.query(CornVariety).filter(CornVariety.id == variety_id).first()
    
    def get_all_corn_varieties(self) -> List[CornVariety]:
        """
        Obtiene todas las variedades de maíz disponibles.

        Returns:
            List[CornVariety]: Lista de todas las variedades de maíz.
        """
        return self.db.query(CornVariety).all()

    def get_crop_state_by_id(self, state_id: int) -> Optional[CropState]:
        """
        Obtiene un estado de cultivo por su ID.

        Args:
            state_id (int): ID del estado de cultivo.

        Returns:
            Optional[CropState]: El estado de cultivo si se encuentra, None en caso contrario.
        """
        return self.db.query(CropState).filter(CropState.id == state_id).first()

    def get_active_crop_states(self) -> List[CropState]:
        """
        Obtiene los estados que se consideran como cultivos activos.

        Returns:
            List[CropState]: Lista de estados que representan cultivos activos.
        """
        return self.db.query(CropState).filter(
            CropState.nombre.in_([
                'Programado',
                'Sembrado',
                'Germinando',
                'Creciendo',
                'Floración',
                'Maduración'
            ])
        ).all()

    def has_active_crop(self, plot_id: int) -> bool:
        """
        Verifica si un lote tiene un cultivo activo.

        Args:
            plot_id (int): ID del lote.

        Returns:
            bool: True si el lote tiene un cultivo activo, False en caso contrario.
        """
        active_states = self.get_active_crop_states()
        active_state_ids = [state.id for state in active_states]
        
        return self.db.query(Crop).filter(
            Crop.lote_id == plot_id,
            Crop.estado_id.in_(active_state_ids)
        ).first() is not None

    def get_crops_by_plot_id_paginated(self, plot_id: int, page: int, per_page: int) -> tuple[int, List[Crop]]:
        """
        Obtiene todos los cultivos asociados a un lote específico con paginación.

        Args:
            plot_id (int): ID del lote.
            page (int): Número de página.
            per_page (int): Cantidad de elementos por página.

        Returns:
            tuple[List[Crop], int]: Lista de cultivos y total de cultivos.
        """
        query = self.db.query(Crop).filter(Crop.lote_id == plot_id)
        total_crops = query.count()
        crops = query.offset((page - 1) * per_page).limit(per_page).all()
        return total_crops, crops
