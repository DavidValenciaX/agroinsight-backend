from sqlalchemy.orm import Session
from app.plot.infrastructure.orm_models import Plot
from app.plot.domain.schemas import PlotCreate
from typing import Optional
from typing import List, Tuple
from sqlalchemy import func
from decimal import Decimal
from sqlalchemy import update

class PlotRepository:
    """Repositorio para gestionar las operaciones de base de datos relacionadas con los lotes.

    Esta clase proporciona métodos para crear, obtener y listar lotes en la base de datos.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
    """

    def __init__(self, db: Session):
        """Inicializa el repositorio de lotes con la sesión de base de datos.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db

    def create_plot(self, plot_data: PlotCreate) -> Optional[Plot]:
        """Crea un nuevo lote en la base de datos.

        Args:
            plot_data (PlotCreate): Datos del lote a crear.

        Returns:
            Optional[Plot]: El lote creado o None si ocurre un error.
        """
        try:
            new_plot = Plot(
                nombre=plot_data.nombre,
                area=plot_data.area,
                unidad_area_id=plot_data.unidad_area_id,
                latitud=plot_data.latitud,
                longitud=plot_data.longitud,
                finca_id=plot_data.finca_id,
                costos_mantenimiento=plot_data.costos_mantenimiento,
                moneda_id=plot_data.moneda_id
            )
            self.db.add(new_plot)
            self.db.commit()
            self.db.refresh(new_plot)
            return new_plot
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear el lote: {e}")
            return None
        
    def get_plot_by_id(self, plot_id: int) -> Optional[Plot]:
        """Obtiene un lote por su ID.

        Args:
            plot_id (int): ID del lote a buscar.

        Returns:
            Optional[Plot]: El lote encontrado o None si no existe.
        """
        return self.db.query(Plot).filter(Plot.id == plot_id).first()
    
    def list_plots_by_farm_paginated(self, finca_id: int, page: int, per_page: int) -> Tuple[int, List[Plot]]:
        """Lista los lotes de una finca de forma paginada.

        Args:
            finca_id (int): ID de la finca de la cual se quieren listar los lotes.
            page (int): Número de página actual.
            per_page (int): Cantidad de lotes por página.

        Returns:
            Tuple[int, List[Plot]]: Tupla con el total de lotes y la lista de lotes para la página actual.
        """
        query = self.db.query(Plot).filter(Plot.finca_id == finca_id)
        
        total = query.count()
        plots = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return total, plots
    
    def list_plots(self) -> List[Plot]:
        """Lista todos los lotes."""
        return self.db.query(Plot).all()
    
    def get_plot_by_name_and_farm(self, nombre: str, finca_id: int) -> Optional[Plot]:
        """Obtiene un lote por su nombre y el ID de la finca.

        Args:
            nombre (str): Nombre del lote a buscar.
            finca_id (int): ID de la finca a la que pertenece el lote.

        Returns:
            Optional[Plot]: El lote encontrado o None si no existe.
        """
        return self.db.query(Plot).filter(
            Plot.nombre == nombre,
            Plot.finca_id == finca_id
        ).first()
    
    def update_maintenance_costs(self, plot_id: int, additional_cost: Decimal) -> bool:
        """Actualiza los costos de mantenimiento de un lote sumando el nuevo costo.

        Args:
            plot_id (int): ID del lote
            additional_cost (Decimal): Costo adicional a sumar

        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        try:
            stmt = update(Plot).where(Plot.id == plot_id).\
                values(costos_mantenimiento=Plot.costos_mantenimiento + additional_cost)
            self.db.execute(stmt)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al actualizar los costos de mantenimiento: {e}")
            return False