from sqlalchemy.orm import Session
from app.farm.domain.schemas import FarmCreate
from app.farm.infrastructure.orm_models import Farm
from typing import Optional, List, Tuple
from typing import List
from app.user.infrastructure.orm_models import User, UserFarmRole
from app.user.infrastructure.sql_repository import UserRepository
from app.user.application.services.user_service import UserService

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