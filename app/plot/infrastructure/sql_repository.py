from sqlalchemy.orm import Session
from app.plot.infrastructure.orm_models import Plot
from app.plot.domain.schemas import PlotCreate
from typing import Optional

class PlotRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_plot(self, plot_data: PlotCreate, user_id: int) -> Optional[Plot]:
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