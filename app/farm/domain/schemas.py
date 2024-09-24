from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from datetime import datetime

class FincaCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    ubicacion: str = Field(..., min_length=1, max_length=255)
    area_total: Decimal = Field(..., gt=0)
    unidad_area_id: int
    latitud: Decimal = Field(..., ge=-90, le=90)
    longitud: Decimal = Field(..., ge=-180, le=180)

class FincaResponse(BaseModel):
    id: int
    nombre: str
    ubicacion: str
    area_total: Decimal
    unidad_area: str
    latitud: Decimal
    longitud: Decimal

    class Config:
        from_attributes = True
        
class CategoriaUnidadMedidaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class CategoriaUnidadMedidaCreate(CategoriaUnidadMedidaBase):
    pass

class CategoriaUnidadMedida(CategoriaUnidadMedidaBase):
    id: int
    fecha_creacion: datetime
    fecha_modificacion: Optional[datetime] = None

    class Config:
        from_attributes = True

class UnidadMedidaBase(BaseModel):
    nombre: str
    abreviatura: str
    categoria_id: int

class UnidadMedidaCreate(UnidadMedidaBase):
    pass

class UnidadMedida(UnidadMedidaBase):
    id: int
    fecha_creacion: datetime
    fecha_modificacion: Optional[datetime] = None

    class Config:
        from_attributes = True