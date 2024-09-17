from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional
from datetime import datetime
from app.core.security.security_utils import validate_password

class UserCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=50)
    apellido: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=12)
    
    @field_validator('password')
    def validate_user_password(cls, v):
        try:
            return validate_password(v)
        except ValueError as e:
            raise ValueError(str(e))
        
class AdminUserCreate(UserCreate):
    role_id: int

class Confirmation(BaseModel):
    usuario_id: int
    pin: str = Field(..., min_length=1, max_length=64)
    expiracion: datetime
    intentos: int = Field(default=0, ge=0)
    
class ConfirmationRequest(BaseModel):
    email: EmailStr
    pin: str

class ResendPinConfirmRequest(BaseModel):
    email: EmailStr
    
class UserCreationResponse(BaseModel):
    message: str

class RoleInfo(BaseModel):
    id: int
    nombre: str

class UserInDB(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: EmailStr
    password: str
    failed_attempts: int
    locked_until: Optional[datetime]
    state_id: int
    roles: List[RoleInfo] = []

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: EmailStr
    estado: str
    rol: str

    class Config:
        from_attributes = True

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    
class TwoFactorAuthRequest(BaseModel):
    email: EmailStr
    pin: str = Field(..., min_length=4, max_length=4)
    
class Resend2FARequest(BaseModel):
    email: EmailStr
    
class TwoFactorAuth(BaseModel):
    usuario_id: int
    pin: str = Field(..., min_length=1, max_length=64)
    expiracion: datetime
    intentos: int = Field(default=0, ge=0)
    
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    
class UserUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=50)
    apellido: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[EmailStr]

    class Config:
        from_attributes = True
        
class AdminUserUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=50)
    apellido: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[EmailStr]
    estado_id: Optional[int]  # Ahora es el ID del estado
    rol_id: Optional[int]     # Ahora es el ID del rol

    class Config:
        from_attributes = True
    
class PasswordRecovery(BaseModel):
    usuario_id: int
    pin: str = Field(..., min_length=1, max_length=64)
    expiracion: datetime
    intentos: int = Field(default=0, ge=0)

class PasswordRecoveryRequest(BaseModel):
    email: EmailStr

class PinConfirmationRequest(BaseModel):
    email: EmailStr
    pin: str = Field(..., min_length=4, max_length=4)

class PasswordResetRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(..., min_length=12)
    
    @field_validator('new_password')
    def validate_reset_password(cls, v):
        try:
            return validate_password(v)
        except ValueError as e:
            raise ValueError(str(e))
