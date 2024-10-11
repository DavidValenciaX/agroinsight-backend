from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional, List

from app.user.domain.schemas import UserResponse

class FarmCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    ubicacion: str = Field(..., min_length=1, max_length=255)
    area_total: Decimal = Field(..., gt=0)
    unidad_area_id: int
    latitud: Decimal = Field(..., ge=-90, le=90)
    longitud: Decimal = Field(..., ge=-180, le=180)


class FarmResponse(BaseModel):
    id: int
    nombre: str
    ubicacion: str
    area_total: float
    unidad_area: str
    latitud: float
    longitud: float
    usuarios: List[UserResponse]

    class Config:
        from_attributes = True
        
class FarmListResponse(BaseModel):
    farms: List[FarmResponse]
    
class PaginatedFarmListResponse(BaseModel):
    farms: List[FarmResponse]
    total_farms: int
    page: int
    per_page: int
    total_pages: int
        
class UnitCategoryBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class UnitCategoryCreate(UnitCategoryBase):
    pass

class UnitCategory(UnitCategoryBase):
    id: int

    class Config:
        from_attributes = True

class UnitOfMeasureBase(BaseModel):
    nombre: str
    abreviatura: str
    categoria_id: int

class UnitOfMeasureCreate(UnitOfMeasureBase):
    pass

class UnitOfMeasure(UnitOfMeasureBase):
    id: int

    class Config:
        from_attributes = True
        
class FarmUserAssignmentById(BaseModel):
    farm_id: int
    user_ids: List[int]
    
class FarmUserAssignmentByEmail(BaseModel):
    farm_id: int
    user_emails: List[str]
    
class FarmUserListResponse(BaseModel):
    users: List[UserResponse]

class PaginatedFarmUserListResponse(BaseModel):
    users: List[UserResponse]
    total_users: int
    page: int
    per_page: int
    total_pages: int