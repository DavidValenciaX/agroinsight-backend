from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional
from datetime import datetime
import re

class UserCreate(BaseModel):
    email: EmailStr
    nombre: str
    apellido: str
    password: str

    @field_validator('password')
    def validate_password(cls, v):
        errors = []
        if len(v) < 12:
            errors.append('La contraseña debe tener al menos 12 caracteres')
        if not re.search(r'\d', v):
            errors.append('La contraseña debe contener al menos un número')
        if not re.search(r'[a-zA-Z]', v):
            errors.append('La contraseña debe contener al menos una letra')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            errors.append('La contraseña debe contener al menos un caracter especial')
        
        if errors:
            raise ValueError("; ".join(errors))
        return v
        
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
    def validate_password(cls, v):
        errors = []
        if len(v) < 12:
            errors.append('La contraseña debe tener al menos 12 caracteres')
        if not re.search(r'\d', v):
            errors.append('La contraseña debe contener al menos un número')
        if not re.search(r'[a-zA-Z]', v):
            errors.append('La contraseña debe contener al menos una letra')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            errors.append('La contraseña debe contener al menos un caracter especial')
        
        if errors:
            raise ValueError("; ".join(errors))
        return v
