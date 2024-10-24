from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationError
from decimal import Decimal
from typing import List
from app.infrastructure.utils.validators import validate_email_format, validate_no_emojis
from app.user.domain.schemas import UserForFarmResponse

class FarmCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    ubicacion: str = Field(..., min_length=2, max_length=255)
    area_total: Decimal = Field(..., gt=0)
    unidad_area_id: int
    
    _validate_no_emojis = field_validator('nombre')(validate_no_emojis)
    _validate_no_emojis = field_validator('ubicacion')(validate_no_emojis)

class FarmResponse(BaseModel):
    id: int
    nombre: str
    ubicacion: str
    area_total: float
    unidad_area: str
    usuarios: List[UserForFarmResponse]

    model_config = ConfigDict(from_attributes=True)
    
class PaginatedFarmListResponse(BaseModel):
    farms: List[FarmResponse]
    total_farms: int
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1, le=100)
    total_pages: int
    
class FarmUserAssignmentByEmail(BaseModel):
    farm_id: int
    user_emails: List[str]
    
    @field_validator('user_emails')
    def validate_emails(cls, emails):
        validation_errors = []
        for email in emails:
            try:
                validate_email_format(email)
            except ValueError as e:
                validation_errors.append(f"Email '{email}': {str(e)}")
        
        if validation_errors:
            raise ValueError(validation_errors)
        return emails

class PaginatedFarmUserListResponse(BaseModel):
    users: List[UserForFarmResponse]
    total_users: int
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1, le=100)
    total_pages: int
