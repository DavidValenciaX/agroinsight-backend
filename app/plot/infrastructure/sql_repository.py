from sqlalchemy.orm import Session
from app.plot.infrastructure.orm_models import Plot
from app.plot.domain.schemas import PlotCreate
from typing import Optional
from app.user.infrastructure.orm_models import UserFarmRole
from app.farm.infrastructure.orm_models import Farm
from typing import List, Tuple
from sqlalchemy import func

class PlotRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_plot(self, plot_data: PlotCreate) -> Optional[Plot]:
        try:
            new_plot = Plot(
                nombre=plot_data.nombre,
                area=plot_data.area,
                unidad_area_id=plot_data.unidad_area_id,
                latitud=plot_data.latitud,
                longitud=plot_data.longitud,
                finca_id=plot_data.finca_id
            )
            self.db.add(new_plot)
            self.db.commit()
            self.db.refresh(new_plot)
            return new_plot
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear el lote: {e}")
            return None
        
    def list_plots(self, user_id: int) -> List[Plot]:
            return self.db.query(Plot).join(UserFarmRole, Plot.finca_id == UserFarmRole.finca_id).filter(UserFarmRole.usuario_id == user_id).all()
        
    def list_plots_by_farm(self, finca_id: int) -> List[Plot]:
        return self.db.query(Plot).filter(Plot.finca_id == finca_id).all()
    
    def list_plots_by_farm_paginated(self, finca_id: int, page: int, per_page: int) -> Tuple[int, List[Plot]]:
        query = self.db.query(Plot).filter(Plot.finca_id == finca_id)
        
        total = query.count()
        plots = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return total, plots
    
    def get_farm_by_id(self, finca_id: int) -> Optional[Farm]:
        return self.db.query(Farm).filter(Farm.id == finca_id).first()

    def check_user_farm_access(self, user_id: int, finca_id: int) -> bool:
        access = self.db.query(UserFarmRole).filter(
            UserFarmRole.usuario_id == user_id,
            UserFarmRole.finca_id == finca_id
        ).first()
        return access is not None
    
    def get_plot_by_name_and_farm(self, nombre: str, finca_id: int) -> Optional[Plot]:
        return self.db.query(Plot).filter(
            Plot.nombre == nombre,
            Plot.finca_id == finca_id
        ).first()
        
    def plot_exists(self, plot_id: int) -> bool:
        return self.db.query(Plot).filter(Plot.id == plot_id).first() is not None

    def get_farm_id_by_plot_id(self, plot_id: int) -> int:
        result = self.db.query(Plot.finca_id).filter(Plot.id == plot_id).first()
        return result[0] if result else None