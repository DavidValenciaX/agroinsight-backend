from app.costs.domain.schemas import LaborCostCreate, TaskInputCreate, TaskMachineryCreate
from app.costs.infrastructure.orm_models import LaborCost, TaskInput, TaskMachinery
from decimal import Decimal
from typing import Optional, List, Tuple, Optional
from app.costs.infrastructure.orm_models import AgriculturalInput
from app.costs.infrastructure.orm_models import AgriculturalMachinery
from app.costs.infrastructure.orm_models import AgriculturalInputCategory
from app.costs.infrastructure.orm_models import MachineryType
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

class CostsRepository:
    """Repositorio para gestionar las operaciones de base de datos relacionadas con costos.

    Este repositorio proporciona métodos para interactuar con las tareas y asignaciones de costos.

    Attributes:
        db (Session): Sesión de base de datos SQLAlchemy.
    """

    def __init__(self, db: Session):
        """Inicializa el repositorio con la sesión de base de datos.

        Args:
            db (Session): Sesión de base de datos SQLAlchemy.
        """
        self.db = db

    def create_labor_cost(self, task_id: int, labor_cost: LaborCostCreate) -> bool:
        """Crea un registro de costo de mano de obra para una tarea."""
        try:
            costo_total = labor_cost.cantidad_trabajadores * labor_cost.horas_trabajadas * labor_cost.costo_hora
            new_labor_cost = LaborCost(
                tarea_labor_id=task_id,
                cantidad_trabajadores=labor_cost.cantidad_trabajadores,
                horas_trabajadas=labor_cost.horas_trabajadas,
                costo_hora=labor_cost.costo_hora,
                costo_total=costo_total,
                observaciones=labor_cost.observaciones
            )
            self.db.add(new_labor_cost)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear el costo de mano de obra: {e}")
            return False

    def create_task_input(self, task_id: int, input_data: TaskInputCreate, costo_total: Decimal) -> bool:
        """Crea un registro de uso de insumo para una tarea."""
        try:
            new_task_input = TaskInput(
                tarea_labor_id=task_id,
                insumo_id=input_data.insumo_id,
                cantidad_utilizada=input_data.cantidad_utilizada,
                costo_total=costo_total,
                fecha_aplicacion=input_data.fecha_aplicacion,
                observaciones=input_data.observaciones
            )
            self.db.add(new_task_input)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear el registro de insumo: {e}")
            return False

    def create_task_machinery(self, task_id: int, machinery_data: TaskMachineryCreate, costo_total: Decimal) -> bool:
        """Crea un registro de uso de maquinaria para una tarea."""
        try:
            new_task_machinery = TaskMachinery(
                tarea_labor_id=task_id,
                maquinaria_id=machinery_data.maquinaria_id,
                fecha_uso=machinery_data.fecha_uso,
                horas_uso=machinery_data.horas_uso,
                costo_total=costo_total,
                observaciones=machinery_data.observaciones
            )
            self.db.add(new_task_machinery)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear el registro de maquinaria: {e}")
            return False

    def get_input_cost(self, input_id: int) -> Optional[Decimal]:
        """Obtiene el costo unitario de un insumo."""
        result = self.db.query(AgriculturalInput.costo_unitario).filter(
            AgriculturalInput.id == input_id
        ).first()
        return result[0] if result else None

    def get_machinery_cost_per_hour(self, machinery_id: int) -> Optional[Decimal]:
        """Obtiene el costo por hora de una maquinaria."""
        result = self.db.query(AgriculturalMachinery.costo_hora).filter(
            AgriculturalMachinery.id == machinery_id
        ).first()
        return result[0] if result else None

    def get_input_categories(self) -> List[AgriculturalInputCategory]:
        """Obtiene todas las categorías de insumos agrícolas.

        Returns:
            List[AgriculturalInputCategory]: Lista de todas las categorías de insumos.
        """
        return self.db.query(AgriculturalInputCategory).all()

    def get_agricultural_inputs(self) -> List[AgriculturalInput]:
        """Obtiene todos los insumos agrícolas.

        Returns:
            List[AgriculturalInput]: Lista de todos los insumos agrícolas.
        """
        return self.db.query(AgriculturalInput)\
            .options(joinedload(AgriculturalInput.categoria))\
            .options(joinedload(AgriculturalInput.unidad_medida))\
            .all()

    def get_machinery_types(self) -> List[MachineryType]:
        """Obtiene todos los tipos de maquinaria agrícola.

        Returns:
            List[MachineryType]: Lista de todos los tipos de maquinaria.
        """
        return self.db.query(MachineryType).all()
    
    def get_agricultural_machinery(self) -> List[AgriculturalMachinery]:
        """Obtiene toda la maquinaria agrícola.

        Returns:
            List[AgriculturalMachinery]: Lista de toda la maquinaria agrícola.
        """
        return self.db.query(AgriculturalMachinery)\
            .options(joinedload(AgriculturalMachinery.tipo_maquinaria))\
            .all()

    def get_input_by_id(self, input_id: int) -> Optional[AgriculturalInput]:
        """Obtiene un insumo agrícola por su ID.

        Args:
            input_id (int): ID del insumo.

        Returns:
            Optional[AgriculturalInput]: El insumo encontrado o None.
        """
        return self.db.query(AgriculturalInput)\
            .options(joinedload(AgriculturalInput.categoria))\
            .filter(AgriculturalInput.id == input_id)\
            .first()
            
    def get_task_costs(self, task_id: int) -> Tuple[Decimal, Decimal, Decimal]:
        """Obtiene los costos de una tarea específica"""
        # Costo mano de obra
        labor_cost = self.db.query(func.coalesce(func.sum(LaborCost.costo_total), 0))\
            .filter(LaborCost.tarea_labor_id == task_id)\
            .scalar()

        # Costo insumos
        input_cost = self.db.query(func.coalesce(func.sum(TaskInput.costo_total), 0))\
            .filter(TaskInput.tarea_labor_id == task_id)\
            .scalar()

        # Costo maquinaria
        machinery_cost = self.db.query(func.coalesce(func.sum(TaskMachinery.costo_total), 0))\
            .filter(TaskMachinery.tarea_labor_id == task_id)\
            .scalar()

        return labor_cost, input_cost, machinery_cost
