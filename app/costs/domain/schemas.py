from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from typing import List, Optional
from decimal import Decimal

class LaborCostCreate(BaseModel):
    """Modelo para la creación de costos de mano de obra.

    Attributes:
        cantidad_trabajadores (int): Número de trabajadores.
        horas_trabajadas (Decimal): Horas trabajadas.
        costo_hora (Decimal): Costo por hora.
        observaciones (Optional[str]): Observaciones adicionales.
        moneda_id (Optional[int]): ID de la moneda.
    """
    cantidad_trabajadores: int = Field(..., gt=0)
    horas_trabajadas: Decimal = Field(..., gt=0)
    costo_hora: Decimal = Field(..., gt=0)
    observaciones: Optional[str] = None
    moneda_id: Optional[int] = None

class TaskInputCreate(BaseModel):
    """Modelo para la creación de costos de insumos.

    Attributes:
        insumo_id (int): ID del insumo utilizado.
        cantidad_utilizada (Decimal): Cantidad utilizada del insumo.
        fecha_aplicacion (date): Fecha de aplicación del insumo.
        observaciones (Optional[str]): Observaciones adicionales.
    """
    insumo_id: int
    cantidad_utilizada: Decimal = Field(..., gt=0)
    fecha_aplicacion: Optional[date] = None
    observaciones: Optional[str] = None

class TaskMachineryCreate(BaseModel):
    """Modelo para la creación de costos de maquinaria.

    Attributes:
        maquinaria_id (int): ID de la maquinaria utilizada.
        fecha_uso (date): Fecha de uso de la maquinaria.
        horas_uso (Decimal): Horas de uso de la maquinaria.
        observaciones (Optional[str]): Observaciones adicionales.
    """
    maquinaria_id: int
    fecha_uso: Optional[date] = None
    horas_uso: Decimal = Field(..., gt=0)
    observaciones: Optional[str] = None

class TaskCostsCreate(BaseModel):
    """Modelo para la creación de todos los costos asociados a una tarea.

    Attributes:
        labor_cost (Optional[LaborCostCreate]): Costos de mano de obra.
        inputs (Optional[List[TaskInputCreate]]): Lista de insumos utilizados.
        machinery (Optional[List[TaskMachineryCreate]]): Lista de maquinaria utilizada.
    """
    labor_cost: Optional[LaborCostCreate] = None
    inputs: Optional[List[TaskInputCreate]] = None
    machinery: Optional[List[TaskMachineryCreate]] = None

class CostRegistrationResponse(BaseModel):
    """Modelo de respuesta para el registro de costos.

    Attributes:
        message: str: Mensaje de éxito.
        labor_cost_registered: bool: Indica si se registraron costos de mano de obra.
        inputs_registered: int: Cantidad de insumos registrados.
        machinery_registered: int: Cantidad de maquinaria registrada.
    """
    message: str
    labor_cost_registered: bool
    inputs_registered: int
    machinery_registered: int

class AgriculturalInputCategoryResponse(BaseModel):
    """Modelo de respuesta para una categoría de insumo agrícola.

    Attributes:
        id (int): ID único de la categoría.
        nombre (str): Nombre de la categoría.
        descripcion (Optional[str]): Descripción de la categoría.
    """
    id: int
    nombre: str
    descripcion: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AgriculturalInputCategoryListResponse(BaseModel):
    """Modelo de respuesta para la lista de categorías de insumos agrícolas.

    Attributes:
        categories (List[AgriculturalInputCategoryResponse]): Lista de categorías de insumos.
    """
    categories: List[AgriculturalInputCategoryResponse]

class AgriculturalInputResponse(BaseModel):
    """Modelo de respuesta para un insumo agrícola.

    Attributes:
        id (int): ID único del insumo.
        categoria_id (int): ID de la categoría del insumo.
        categoria_nombre (str): Nombre de la categoría del insumo.
        nombre (str): Nombre del insumo.
        descripcion (Optional[str]): Descripción del insumo.
        unidad_medida_id (int): ID de la unidad de medida.
        unidad_medida_nombre (str): Nombre de la unidad de medida.
        costo_unitario (Decimal): Costo por unidad del insumo.
        stock_actual (Decimal): Cantidad actual en stock.
        moneda_id (int): ID de la moneda.
        moneda_simbolo (str): Símbolo de la moneda.
    """
    id: int
    categoria_id: int
    categoria_nombre: str
    nombre: str
    descripcion: Optional[str] = None
    unidad_medida_id: int
    unidad_medida_nombre: str
    costo_unitario: Decimal
    stock_actual: Decimal
    moneda_id: int
    moneda_simbolo: str

    model_config = ConfigDict(from_attributes=True)

class AgriculturalInputListResponse(BaseModel):
    """Modelo de respuesta para la lista de insumos agrícolas.

    Attributes:
        inputs (List[AgriculturalInputResponse]): Lista de insumos agrícolas.
    """
    inputs: List[AgriculturalInputResponse]

class MachineryTypeResponse(BaseModel):
    """Modelo de respuesta para un tipo de maquinaria.

    Attributes:
        id (int): ID único del tipo de maquinaria.
        nombre (str): Nombre del tipo de maquinaria.
        descripcion (str): Descripción del tipo de maquinaria.
    """
    id: int
    nombre: str
    descripcion: str

    model_config = ConfigDict(from_attributes=True)

class MachineryTypeListResponse(BaseModel):
    """Modelo de respuesta para la lista de tipos de maquinaria.

    Attributes:
        machinery_types (List[MachineryTypeResponse]): Lista de tipos de maquinaria.
    """
    machinery_types: List[MachineryTypeResponse]

class AgriculturalMachineryResponse(BaseModel):
    """Modelo de respuesta para una maquinaria agrícola.

    Attributes:
        id (int): ID único de la maquinaria.
        tipo_maquinaria_id (int): ID del tipo de maquinaria.
        tipo_maquinaria_nombre (str): Nombre del tipo de maquinaria.
        nombre (str): Nombre de la maquinaria.
        descripcion (Optional[str]): Descripción de la maquinaria.
        modelo (Optional[str]): Modelo de la maquinaria.
        numero_serie (Optional[str]): Número de serie de la maquinaria.
        costo_hora (Decimal): Costo por hora de la maquinaria.
        moneda_id (int): ID de la moneda.
        moneda_simbolo (str): Símbolo de la moneda.
    """
    id: int
    tipo_maquinaria_id: int
    tipo_maquinaria_nombre: str
    nombre: str
    descripcion: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    costo_hora: Decimal
    moneda_id: int
    moneda_simbolo: str

    model_config = ConfigDict(from_attributes=True)

class AgriculturalMachineryListResponse(BaseModel):
    """Modelo de respuesta para la lista de maquinaria agrícola.

    Attributes:
        machinery (List[AgriculturalMachineryResponse]): Lista de maquinaria agrícola.
    """
    machinery: List[AgriculturalMachineryResponse]
