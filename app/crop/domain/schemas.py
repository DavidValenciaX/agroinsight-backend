from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import date
from typing import List, Optional
from decimal import Decimal

class CropCreate(BaseModel):
    """Schema para la creación de un cultivo.

    Este modelo define los datos necesarios para crear un cultivo en el sistema.

    Attributes:
        lote_id (int): ID del lote al que pertenece el cultivo. Debe ser mayor que 0.
        variedad_maiz_id (int): ID de la variedad de maíz. Debe ser mayor que 0.
        fecha_siembra (date): Fecha en la que se siembra el cultivo.
        densidad_siembra (int): Densidad de siembra del cultivo. Debe ser mayor que 0.
        densidad_siembra_unidad_id (int): ID de la unidad de medida de la densidad de siembra. Debe ser mayor que 0.
        estado_id (int): ID del estado del cultivo. Debe ser mayor que 0.
        moneda_id (Optional[int]): ID de la moneda utilizada. Debe ser mayor que 0.
    """
    lote_id: int = Field(..., gt=0)
    variedad_maiz_id: int = Field(..., gt=0)
    fecha_siembra: date
    densidad_siembra: int = Field(..., gt=0)
    densidad_siembra_unidad_id: int = Field(..., gt=0)
    estado_id: int = Field(..., gt=0)
    moneda_id: Optional[int] = None

class CropResponse(BaseModel):
    """Schema para la respuesta con información de un cultivo.

    Este modelo define la estructura de la respuesta que incluye los detalles de un cultivo.

    Attributes:
        id (int): Identificador único del cultivo.
        lote_id (int): ID del lote al que pertenece el cultivo.
        variedad_maiz_id (int): ID de la variedad de maíz.
        variedad_maiz_nombre (str): Nombre de la variedad de maíz.
        fecha_siembra (date): Fecha en la que se siembra el cultivo.
        densidad_siembra (int): Densidad de siembra del cultivo.
        densidad_siembra_unidad_id (int): ID de la unidad de medida de la densidad de siembra.
        estado_id (int): ID del estado del cultivo.
        fecha_cosecha (Optional[date]): Fecha de cosecha del cultivo, si está disponible.
        produccion_total (Optional[int]): Producción total del cultivo, si está disponible.
        produccion_total_unidad_id (Optional[int]): ID de la unidad de medida de la producción total, si está disponible.
        precio_venta_unitario (Optional[Decimal]): Precio de venta unitario del cultivo, si está disponible.
        cantidad_vendida (Optional[int]): Cantidad vendida del cultivo, si está disponible.
        cantidad_vendida_unidad_id (Optional[int]): ID de la unidad de medida de la cantidad vendida, si está disponible.
        ingreso_total (Optional[Decimal]): Ingreso total generado por la venta del cultivo, si está disponible.
        costo_produccion (Optional[Decimal]): Costo de producción del cultivo, si está disponible.
        moneda_id (Optional[int]): ID de la moneda utilizada, si está disponible.
        fecha_venta (Optional[date]): Fecha de venta del cultivo, si está disponible.
    """
    id: int
    lote_id: int
    variedad_maiz_id: int
    variedad_maiz_nombre: str
    fecha_siembra: date
    densidad_siembra: int
    densidad_siembra_unidad_id: int
    estado_id: int
    fecha_cosecha: Optional[date]
    produccion_total: Optional[int]
    produccion_total_unidad_id: Optional[int]
    precio_venta_unitario: Optional[Decimal]
    cantidad_vendida: Optional[int]
    cantidad_vendida_unidad_id: Optional[int]
    ingreso_total: Optional[Decimal]
    costo_produccion: Optional[Decimal]
    moneda_id: Optional[int]
    fecha_venta: Optional[date]

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    @classmethod
    def extract_corn_variety_name(cls, data):
        if hasattr(data, '__dict__'):
            # Extract the corn variety name from the relationship
            if hasattr(data, 'variedad_maiz') and data.variedad_maiz:
                data = data.__dict__
                data['variedad_maiz_nombre'] = data['variedad_maiz'].nombre
        return data

class PaginatedCropListResponse(BaseModel):
    """Schema para la respuesta paginada de la lista de cultivos.

    Este modelo define la estructura de la respuesta que incluye una lista de cultivos
    y la información de paginación.

    Attributes:
        crops (List[CropResponse]): Lista de cultivos para la página actual.
        total_crops (int): Número total de cultivos.
        page (int): Número de página actual. Debe ser mayor o igual a 1.
        per_page (int): Cantidad de elementos por página. Debe ser mayor o igual a 1 y menor o igual a 100.
        total_pages (int): Número total de páginas.
    """
    crops: List[CropResponse]
    total_crops: int
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1, le=100)
    total_pages: int

class CornVarietyResponse(BaseModel):
    """Schema para la respuesta con información de una variedad de maíz.

    Este modelo define la estructura de la respuesta que incluye los detalles de una variedad de maíz.

    Attributes:
        id (int): Identificador único de la variedad de maíz.
        nombre (str): Nombre de la variedad de maíz.
        descripcion (Optional[str]): Descripción de la variedad de maíz, si está disponible.
    """
    id: int
    nombre: str
    descripcion: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class CornVarietyListResponse(BaseModel):
    """Schema para la respuesta con la lista de variedades de maíz.

    Este modelo define la estructura de la respuesta que incluye una lista de variedades de maíz.

    Attributes:
        varieties (List[CornVarietyResponse]): Lista de variedades de maíz.
    """
    varieties: List[CornVarietyResponse]

class CropHarvestUpdate(BaseModel):
    """Schema para actualizar la información de cosecha y venta de un cultivo.

    Attributes:
        fecha_cosecha (date): Fecha en que se realizó la cosecha.
        produccion_total (int): Cantidad total producida. Debe ser mayor que 0.
        produccion_total_unidad_id (int): ID de la unidad de medida de la producción total. Debe ser mayor que 0.
        precio_venta_unitario (Decimal): Precio de venta por unidad.
        cantidad_vendida (int): Cantidad vendida del cultivo. Debe ser mayor que 0.
        cantidad_vendida_unidad_id (int): ID de la unidad de medida de la cantidad vendida. Debe ser mayor que 0.
        moneda_id (Optional[int]): ID de la moneda utilizada. Si no se especifica, se usará COP por defecto.
        fecha_venta (date): Fecha en que se realizó la venta.
    """
    fecha_cosecha: date
    produccion_total: int = Field(..., gt=0)
    produccion_total_unidad_id: int = Field(..., gt=0)
    precio_venta_unitario: Decimal = Field(..., gt=0)
    cantidad_vendida: int = Field(..., gt=0)
    cantidad_vendida_unidad_id: int = Field(..., gt=0)
    moneda_id: Optional[int] = None
    fecha_venta: date
