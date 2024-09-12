import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional
from datetime import datetime

class UserCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=50)
    apellido: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=12)
    
    @field_validator('password')
    def validate_password(cls, v):
        # Longitud mínima
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters long')

        # Debe contener al menos un número
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')

        # Debe contener al menos una letra
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('Password must contain at least one letter')

        # Debe contener al menos un símbolo especial
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')

        return v

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

class UserCreationResponse(BaseModel):
    message: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    
class ConfirmationRequest(BaseModel):
    email: EmailStr
    pin: str

class TwoFactorAuthRequest(BaseModel):
    email: EmailStr
    pin: str = Field(..., min_length=4, max_length=4)
    
class ResendPinRequest(BaseModel):
    email: EmailStr
    
class Resend2FARequest(BaseModel):
    email: EmailStr
    
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
        # Longitud mínima
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters long')

        # Debe contener al menos un número
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')

        # Debe contener al menos una letra
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('Password must contain at least one letter')

        # Debe contener al menos un símbolo especial
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')

        return v
