from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from typing import List

from app.user.domain.schemas import UserResponse

class FarmCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    ubicacion: str = Field(..., min_length=1, max_length=255)
    area_total: Decimal = Field(..., gt=0)
    unidad_area_id: int


class FarmResponse(BaseModel):
    id: int
    nombre: str
    ubicacion: str
    area_total: float
    unidad_area: str
    usuarios: List[UserResponse]

    model_config = ConfigDict(from_attributes=True)
    
class PaginatedFarmListResponse(BaseModel):
    farms: List[FarmResponse]
    total_farms: int
    page: int
    per_page: int
    total_pages: int
    
class FarmUserAssignmentByEmail(BaseModel):
    farm_id: int
    user_emails: List[str]

class PaginatedFarmUserListResponse(BaseModel):
    users: List[UserResponse]
    total_users: int
    page: int
    per_page: int
    total_pages: int