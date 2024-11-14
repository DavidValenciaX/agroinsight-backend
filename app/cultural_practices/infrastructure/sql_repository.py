from typing import List
from sqlalchemy.orm import Session
from app.cultural_practices.domain.schemas import AssignmentCreateSingle, TaskCreate
from app.cultural_practices.infrastructure.orm_models import Assignment, CulturalTaskState, CulturalTaskType, CulturalTask
from app.plot.infrastructure.orm_models import Plot
from sqlalchemy.orm import joinedload

class CulturalPracticesRepository:
    """Repositorio para gestionar las operaciones de base de datos relacionadas con prácticas culturales.

    Este repositorio proporciona métodos para interactuar con las tareas y asignaciones de prácticas culturales.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
    """

    def __init__(self, db: Session):
        """Inicializa el repositorio con la sesión de base de datos.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db
    
    def get_task_type_by_id(self, tipo_labor_id: int) -> CulturalTaskType:
        """Obtiene un tipo de tarea por su ID.

        Args:
            tipo_labor_id (int): ID del tipo de tarea.

        Returns:
            CulturalTaskType: Tipo de tarea correspondiente al ID proporcionado.
        """
        return self.db.query(CulturalTaskType).filter(CulturalTaskType.id == tipo_labor_id).first()
    
    def get_task_type_by_name(self, tipo_labor_nombre: str) -> CulturalTaskType:
        """Obtiene un tipo de tarea por su nombre.

        Args:
            tipo_labor_nombre (str): Nombre del tipo de tarea.

        Returns:
            CulturalTaskType: Tipo de tarea correspondiente al nombre proporcionado.
        """
        return self.db.query(CulturalTaskType).filter(CulturalTaskType.nombre == tipo_labor_nombre).first()
    
    def get_task_state_by_id(self, estado_id: int) -> CulturalTaskState:
        """Obtiene un estado de tarea por su ID.

        Args:
            estado_id (int): ID del estado de la tarea.

        Returns:
            CulturalTaskState: Estado de tarea correspondiente al ID proporcionado.
        """
        return self.db.query(CulturalTaskState).filter(CulturalTaskState.id == estado_id).first()
    
    def get_task_state_by_name(self, estado_nombre: str) -> CulturalTaskState:
        """Obtiene un estado de tarea por su nombre.

        Args:
            estado_nombre (str): Nombre del estado de la tarea.

        Returns:
            CulturalTaskState: Estado de tarea correspondiente al nombre proporcionado.
        """
        return self.db.query(CulturalTaskState).filter(CulturalTaskState.nombre == estado_nombre).first()
    
    def get_task_by_id(self, task_id: int) -> CulturalTask:
        """Obtiene una tarea por su ID.

        Args:
            task_id (int): ID de la tarea.

        Returns:
            CulturalTask: Tarea correspondiente al ID proporcionado.
        """
        return self.db.query(CulturalTask)\
            .options(joinedload(CulturalTask.tipo_labor))\
            .options(joinedload(CulturalTask.estado))\
            .filter(CulturalTask.id == task_id)\
            .first()
    
    def get_states(self) -> List[CulturalTaskState]:
        """Obtiene todos los estados de las tareas.

        Returns:
            List[CulturalTaskState]: Lista de todos los estados de tareas.
        """
        return self.db.query(CulturalTaskState).all()

    def create_task(self, task_data: TaskCreate) -> CulturalTask:
        """Crea una nueva tarea en la base de datos.

        Args:
            task_data (TaskCreate): Datos de la tarea a crear.

        Returns:
            CulturalTask: La tarea creada, o None si hubo un error.
        """
        try:
            new_task = CulturalTask(
                nombre=task_data.nombre,
                tipo_labor_id=task_data.tipo_labor_id,
                fecha_inicio_estimada=task_data.fecha_inicio_estimada,
                descripcion=task_data.descripcion,
                estado_id=task_data.estado_id,
                lote_id=task_data.lote_id
            )
            self.db.add(new_task)
            self.db.commit()
            self.db.refresh(new_task)
            return new_task
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear la tarea: {e}")
            return None
        
    def update_task(self, task: TaskCreate) -> bool:
        """Actualiza una tarea existente en la base de datos.

        Args:
            task (TaskCreate): Datos de la tarea a actualizar.

        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario.
        """
        try:
            self.db.commit()
            self.db.refresh(task)
            return True
        except Exception as e:
            self.db.rollback()
            return False

    def create_assignment(self, assignment_data_single: AssignmentCreateSingle) -> Assignment:
        """Crea una nueva asignación en la base de datos.

        Args:
            assignment_data_single (AssignmentCreateSingle): Datos de la asignación a crear.

        Returns:
            Assignment: La asignación creada, o None si hubo un error.
        """
        try:
            new_assignment = Assignment(
                usuario_id=assignment_data_single.usuario_id,
                tarea_labor_cultural_id=assignment_data_single.tarea_labor_cultural_id
            )
            self.db.add(new_assignment)
            self.db.commit()
            self.db.refresh(new_assignment)
            return new_assignment
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear la asignación: {e}")
            return None
    
    def get_user_task_assignment(self, user_id: int, task_id: int) -> Assignment:
        """Obtiene la asignación de una tarea para un usuario específico.

        Args:
            user_id (int): ID del usuario.
            task_id (int): ID de la tarea.

        Returns:
            Assignment: La asignación correspondiente, o None si no existe.
        """
        return self.db.query(Assignment).filter(
            Assignment.usuario_id == user_id, 
            Assignment.tarea_labor_cultural_id == task_id
        ).first()
        
    def list_tasks_by_user_and_farm_paginated(self, user_id: int, farm_id: int, page: int, per_page: int) -> tuple[int, List[CulturalTask]]:
        """Lista las tareas asignadas a un usuario en una finca específica de forma paginada.

        Args:
            user_id (int): ID del usuario.
            farm_id (int): ID de la finca.
            page (int): Número de página.
            per_page (int): Cantidad de tareas por página.

        Returns:
            tuple[int, List[CulturalTask]]: Tupla con el total de tareas y la lista de tareas para la página actual.
        """
        query = self.db.query(CulturalTask).join(Assignment).join(Plot).filter(
            Assignment.usuario_id == user_id,
            Plot.finca_id == farm_id
        )
        total_tasks = query.count()
        tasks = query.offset((page - 1) * per_page).limit(per_page).all()
        return total_tasks, tasks

    def get_task_types(self) -> List[CulturalTaskType]:
        """Obtiene todos los tipos de tareas de labor cultural.

        Returns:
            List[CulturalTaskType]: Lista de todos los tipos de tareas.
        """
        return self.db.query(CulturalTaskType).all()

    def list_tasks_by_plot_paginated(self, plot_id: int, page: int, per_page: int) -> tuple[int, List[CulturalTask]]:
        """Lista las tareas de un lote específico de forma paginada.

        Args:
            plot_id (int): ID del lote.
            page (int): Número de página.
            per_page (int): Cantidad de tareas por página.

        Returns:
            tuple[int, List[CulturalTask]]: Tupla con el total de tareas y la lista de tareas para la página actual.
        """
        query = self.db.query(CulturalTask)\
            .options(joinedload(CulturalTask.tipo_labor))\
            .options(joinedload(CulturalTask.estado))\
            .filter(CulturalTask.lote_id == plot_id)
        
        total_tasks = query.count()
        tasks = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return total_tasks, tasks

