from typing import List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from pydantic_core import PydanticCustomError
from app.user.domain.types import EmailStrCustom, PasswordStrCustom
import re

class UserCreate(BaseModel):
    email: EmailStrCustom
    nombre: str
    apellido: str
    password: PasswordStrCustom

    @field_validator('nombre')
    def validate_nombre(cls, v):
        if len(v) < 2:
            raise PydanticCustomError('nombre_validation','El nombre debe tener al menos 2 caracteres.')
        return v

    @field_validator('apellido')
    def validate_apellido(cls, v):
        if len(v) < 2:
            raise PydanticCustomError('apellido_validation','El apellido debe tener al menos 2 caracteres.')
        return v
        
class AdminUserCreate(UserCreate):
    role_id: int

class Confirmation(BaseModel):
    usuario_id: int
    pin: str
    expiracion: datetime
    intentos: int
    
class ConfirmationRequest(BaseModel):
    email: EmailStrCustom
    pin: str

class ResendPinConfirmRequest(BaseModel):
    email: EmailStrCustom
    
class UserCreationResponse(BaseModel):
    message: str

class RoleInfo(BaseModel):
    id: int
    nombre: str

class UserInDB(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: EmailStrCustom
    password: str
    failed_attempts: int
    locked_until: datetime
    state_id: int
    roles: List[RoleInfo] = []

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: EmailStrCustom
    estado: str
    rol: str

    class Config:
        from_attributes = True

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStrCustom
    password: str
    
class TwoFactorAuthRequest(BaseModel):
    email: EmailStrCustom
    pin: str
    
class Resend2FARequest(BaseModel):
    email: EmailStrCustom
    
class TwoFactorAuth(BaseModel):
    usuario_id: int
    pin: str
    expiracion: datetime
    intentos: int
    
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    
class UserUpdate(BaseModel):
    nombre: str
    apellido: str
    email: EmailStrCustom

    class Config:
        from_attributes = True
        
class AdminUserUpdate(BaseModel):
    nombre: str
    apellido: str
    email: EmailStrCustom
    estado_id: int
    rol_id: int

    class Config:
        from_attributes = True
    
class PasswordRecovery(BaseModel):
    usuario_id: int
    pin: str
    expiracion: datetime
    intentos: int

class PasswordRecoveryRequest(BaseModel):
    email: EmailStrCustom

class PinConfirmationRequest(BaseModel):
    email: EmailStrCustom
    pin: str
class PasswordResetRequest(BaseModel):
    email: EmailStrCustom
    new_password: PasswordStrCustom
