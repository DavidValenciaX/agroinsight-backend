from datetime import date
from sqlalchemy.orm import Session
from app.farm.domain.schemas import FarmCreate
from app.farm.infrastructure.orm_models import Farm
from typing import Optional, List, Tuple
from typing import List
from app.user.infrastructure.orm_models import User, UserFarmRole
from app.user.infrastructure.sql_repository import UserRepository
from app.user.application.services.user_service import UserService
from sqlalchemy import func
from sqlalchemy.sql import text
from app.cultural_practices.infrastructure.orm_models import CulturalTask
from app.plot.infrastructure.orm_models import Plot
from app.crop.infrastructure.orm_models import Crop
from app.costs.infrastructure.orm_models import LaborCost
from app.costs.infrastructure.orm_models import TaskInput
from app.costs.infrastructure.orm_models import AgriculturalInput
from app.costs.infrastructure.orm_models import TaskMachinery
from app.costs.infrastructure.orm_models import AgriculturalMachinery

class FarmRepository:
    """Repositorio para gestionar las operaciones de base de datos relacionadas con fincas.

    Esta clase maneja todas las operaciones CRUD y consultas relacionadas con fincas,
    incluyendo la gestión de roles de usuarios en las fincas.

    Attributes:
        db (Session): Sesión de SQLAlchemy para interactuar con la base de datos.
        user_repository (UserRepository): Repositorio para operaciones relacionadas con usuarios.
        user_service (UserService): Servicio para lógica de negocio relacionada con usuarios.
    """

    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.user_service = UserService(db)
        
    def create_farm(self, farm_data: FarmCreate) -> Optional[Farm]:
        """Crea una nueva finca en la base de datos.

        Args:
            farm_data (FarmCreate): Datos de la finca a crear.

        Returns:
            Optional[Farm]: La finca creada o None si ocurre un error.
        """
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
        """Lista las fincas paginadas asociadas a un usuario con un rol específico.

        Args:
            user_id (int): ID del usuario.
            rol_id (int): ID del rol.
            page (int): Número de página actual.
            per_page (int): Cantidad de elementos por página.

        Returns:
            Tuple[int, List[Farm]]: Tupla con el total de registros y la lista de fincas.
        """
        query = self.db.query(Farm).join(UserFarmRole).filter(
            UserFarmRole.usuario_id == user_id,
            UserFarmRole.rol_id == rol_id
        )
        
        total = query.count()
        farms = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return total, farms
    
    def get_user_farm(self, user_id: int, farm_id: int) -> UserFarmRole:
        """Obtiene la relación entre un usuario y una finca.

        Args:
            user_id (int): ID del usuario.
            farm_id (int): ID de la finca.

        Returns:
            UserFarmRole: Objeto que representa la relación usuario-finca.
        """
        return self.db.query(UserFarmRole).filter(
            UserFarmRole.usuario_id == user_id,
            UserFarmRole.finca_id == farm_id
        ).first()

    def get_farm_by_id(self, farm_id: int) -> Optional[Farm]:
        """Busca una finca por su ID.

        Args:
            farm_id (int): ID de la finca a buscar.

        Returns:
            Optional[Farm]: La finca encontrada o None si no existe.
        """
        return self.db.query(Farm).filter(Farm.id == farm_id).first()
    
    def get_farm_by_name(self, farm_name: str) -> Optional[Farm]:
        """Busca una finca por su nombre.

        Args:
            farm_name (str): Nombre de la finca a buscar.

        Returns:
            Optional[Farm]: La finca encontrada o None si no existe.
        """
        return self.db.query(Farm).filter(Farm.nombre == farm_name).first()
    
    def list_farm_users_paginated(self, farm_id: int, page: int, per_page: int):
        """Lista los usuarios de una finca de forma paginada.

        Args:
            farm_id (int): ID de la finca.
            page (int): Número de página actual.
            per_page (int): Cantidad de elementos por página.

        Returns:
            Tuple[int, List[User]]: Tupla con el total de registros y la lista de usuarios.
        """
        query = self.db.query(User).join(UserFarmRole).filter(UserFarmRole.finca_id == farm_id)
        total = query.count()
        users = query.offset((page - 1) * per_page).limit(per_page).all()
        return total, users
    
    def list_farm_users_by_role_paginated(self, farm_id: int, role_id: int, page: int, per_page: int):
        """Lista los usuarios de una finca filtrados por rol de forma paginada.

        Args:
            farm_id (int): ID de la finca.
            role_id (int): ID del rol.
            page (int): Número de página actual.
            per_page (int): Cantidad de elementos por página.

        Returns:
            Tuple[int, List[User]]: Tupla con el total de registros y la lista de usuarios.
        """
        query = self.db.query(User) \
            .join(UserFarmRole) \
            .filter(
                UserFarmRole.finca_id == farm_id, 
                UserFarmRole.rol_id == role_id
            )
        total = query.count()
        users = query.offset((page - 1) * per_page).limit(per_page).all()
        return total, users
        
    def get_user_farm_role(self, user_id: int, farm_id: int, role_id: int) -> Optional[UserFarmRole]:
        """Obtiene la relación específica entre un usuario, una finca y un rol.

        Args:
            user_id (int): ID del usuario.
            farm_id (int): ID de la finca.
            role_id (int): ID del rol.

        Returns:
            Optional[UserFarmRole]: La relación encontrada o None si no existe.
        """
        return self.db.query(UserFarmRole).filter(
            UserFarmRole.usuario_id == user_id,
            UserFarmRole.finca_id == farm_id,
            UserFarmRole.rol_id == role_id
        ).first()

    def add_user_to_farm_with_role(self, user_id: int, farm_id: int, role_id: int):
        """Agrega un usuario a una finca con un rol específico.

        Args:
            user_id (int): ID del usuario.
            farm_id (int): ID de la finca.
            role_id (int): ID del rol.

        Returns:
            bool: True si la operación fue exitosa, False en caso contrario.
        """
        try:
            user_farm = UserFarmRole(usuario_id=user_id, finca_id=farm_id, rol_id=role_id)
            self.db.add(user_farm)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear al asignar rol a usuario en finca: {e}")
            return False

    def list_farms_by_role(self, user_id: int, rol_id: int) -> List[Farm]:
        """Lista todas las fincas asociadas a un usuario con un rol específico.

        Args:
            user_id (int): ID del usuario.
            rol_id (int): ID del rol.

        Returns:
            List[Farm]: Lista de fincas.
        """
        query = self.db.query(Farm).join(UserFarmRole).filter(
            UserFarmRole.usuario_id == user_id,
            UserFarmRole.rol_id == rol_id
        )
        
        return query.all()

    def get_farms_ranked_by_profit(
        self, 
        user_id: int, 
        admin_role_id: int,
        limit: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Tuple[Farm, float]]:
        """Obtiene las fincas rankeadas por ganancias.
        
        Returns:
            List[Tuple[Farm, float]]: Lista de tuplas (finca, ganancia)
        """
        # Subconsulta para obtener los ingresos por cultivo
        crop_income = self.db.query(
            Plot.finca_id.label('farm_id'),
            func.sum(
                func.coalesce(Crop.cantidad_vendida, 0) * 
                func.coalesce(Crop.precio_venta_unitario, 0)
            ).label('income')
        ).join(
            Crop, Plot.id == Crop.lote_id
        )

        if start_date:
            crop_income = crop_income.filter(Crop.fecha_siembra >= start_date)
        if end_date:
            crop_income = crop_income.filter(Crop.fecha_siembra <= end_date)

        crop_income = crop_income.group_by(Plot.finca_id).subquery()

        # Subconsulta para obtener los costos totales (mano de obra + insumos + maquinaria)
        total_costs = self.db.query(
            Plot.finca_id.label('farm_id'),
            func.sum(
                func.coalesce(LaborCost.costo_total, 0) +
                func.coalesce(
                    TaskInput.cantidad_utilizada * AgriculturalInput.costo_unitario, 
                    0
                ) +
                func.coalesce(
                    TaskMachinery.horas_uso * AgriculturalMachinery.costo_hora,
                    0
                )
            ).label('costs')
        ).join(
            CulturalTask, Plot.id == CulturalTask.lote_id
        ).outerjoin(
            LaborCost, CulturalTask.id == LaborCost.tarea_labor_id
        ).outerjoin(
            TaskInput, CulturalTask.id == TaskInput.tarea_labor_id
        ).outerjoin(
            AgriculturalInput, TaskInput.insumo_id == AgriculturalInput.id
        ).outerjoin(
            TaskMachinery, CulturalTask.id == TaskMachinery.tarea_labor_id
        ).outerjoin(
            AgriculturalMachinery, TaskMachinery.maquinaria_id == AgriculturalMachinery.id
        )

        if start_date:
            total_costs = total_costs.filter(CulturalTask.fecha_inicio_estimada >= start_date)
        if end_date:
            total_costs = total_costs.filter(CulturalTask.fecha_inicio_estimada <= end_date)

        total_costs = total_costs.group_by(Plot.finca_id).subquery()

        # Query principal para obtener las fincas y calcular las ganancias
        query = self.db.query(
            Farm,
            (func.coalesce(crop_income.c.income, 0) - 
             func.coalesce(total_costs.c.costs, 0)).label('profit')
        ).join(
            UserFarmRole
        ).outerjoin(
            crop_income, Farm.id == crop_income.c.farm_id
        ).outerjoin(
            total_costs, Farm.id == total_costs.c.farm_id
        ).filter(
            UserFarmRole.usuario_id == user_id,
            UserFarmRole.rol_id == admin_role_id
        ).group_by(
            Farm.id,
            crop_income.c.income,
            total_costs.c.costs
        ).order_by(
            text('profit DESC')
        ).limit(limit)

        results = query.all()
        return [(farm, float(profit)) for farm, profit in results]

    def get_farms_ranked_by_production(
        self, 
        user_id: int, 
        admin_role_id: int,
        limit: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Tuple[Farm, float]]:
        """Obtiene las fincas rankeadas por producción total.
        
        Returns:
            List[Tuple[Farm, float]]: Lista de tuplas (finca, producción)
        """
        # Query para obtener la producción total por finca
        query = self.db.query(
            Farm,
            func.coalesce(
                func.sum(Crop.produccion_total), 0.0
            ).label('total_production')
        ).join(
            UserFarmRole
        ).join(
            Plot, Farm.id == Plot.finca_id
        ).join(
            Crop, Plot.id == Crop.lote_id
        ).filter(
            UserFarmRole.usuario_id == user_id,
            UserFarmRole.rol_id == admin_role_id
        )

        if start_date:
            query = query.filter(Crop.fecha_siembra >= start_date)
        if end_date:
            query = query.filter(Crop.fecha_siembra <= end_date)

        results = query.group_by(Farm.id)\
            .order_by(text('total_production DESC'))\
            .limit(limit)\
            .all()

        return [(farm, float(production)) for farm, production in results]