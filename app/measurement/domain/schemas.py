from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class UnitCategoryResponse(BaseModel):
    """
    Esquema para la respuesta que contiene información de una categoría de unidad.

    Attributes:
        id (int): Identificador único de la categoría.
        nombre (str): Nombre de la categoría.
        descripcion (Optional[str]): Descripción de la categoría.
    """
    id: int
    nombre: str
    descripcion: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class UnitOfMeasureResponse(BaseModel):
    """
    Esquema para la respuesta que contiene información de una unidad de medida.

    Attributes:
        id (int): Identificador único de la unidad de medida.
        nombre (str): Nombre de la unidad de medida.
        abreviatura (str): Abreviatura de la unidad de medida.
        categoria (UnitCategoryResponse): Categoría a la que pertenece la unidad.
    """
    id: int
    nombre: str
    abreviatura: str
    categoria: UnitCategoryResponse

    model_config = ConfigDict(from_attributes=True)
    
class UnitsListResponse(BaseModel):
    """
    Esquema para la respuesta que contiene una lista de unidades de medida.

    Attributes:
        unidades (List[UnitOfMeasureResponse]): Lista de unidades de medida.
        total (int): Total de unidades de medida.
        mensaje (str): Mensaje de éxito de la operación.
    """
    units: List[UnitOfMeasureResponse]