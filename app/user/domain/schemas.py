import re
from typing import List
from datetime import datetime
from pydantic import BaseModel, field_validator
from pydantic_core import PydanticCustomError

def validate_email(v: str) -> str:
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, v):
        raise PydanticCustomError('email_validation', 'El correo electrónico no es válido. Debe contener un @ y un dominio válido.')
    return v

def validate_password(v: str) -> str:
    errors = []
    if len(v) < 12:
        errors.append('La contraseña debe tener al menos 12 caracteres.')
    if not re.search(r'\d', v):
        errors.append('La contraseña debe contener al menos un número.')
    if not re.search(r'[a-zA-Z]', v):
        errors.append('La contraseña debe contener al menos una letra.')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
        errors.append('La contraseña debe contener al menos un carácter especial.')
    
    if errors:
        message = '\n'.join(errors)
        raise PydanticCustomError('password_validation', message)
    return v

class UserCreate(BaseModel):
    email: str
    nombre: str
    apellido: str
    password: str
    
    _validate_email = field_validator('email')(validate_email)
    _validate_password = field_validator('password')(validate_password)

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

class ResendPinConfirmRequest(BaseModel):
    email: str
    
    _validate_email = field_validator('email')(validate_email)

class ConfirmationRequest(BaseModel):
    email: str
    pin: str
    
    _validate_email = field_validator('email')(validate_email)

class UserCreateByAdmin(UserCreate):
    role_id: int

class RoleInfo(BaseModel):
    id: int
    nombre: str

class UserInDB(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str
    password: str
    failed_attempts: int
    locked_until: datetime
    state_id: int
    roles: List[RoleInfo] = []

    class Config:
        from_attributes = True
        
    _validate_email = field_validator('email')(validate_email)
    _validate_password = field_validator('password')(validate_password)

class UserResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str
    estado: str
    rol: str
    fincas: List[str]  # Add this line to include farm names

    class Config:
        from_attributes = True

    _validate_email = field_validator('email')(validate_email)

class LoginRequest(BaseModel):
    email: str
    password: str
    
    _validate_email = field_validator('email')(validate_email)
    _validate_password = field_validator('password')(validate_password)
    
class TwoFactorAuthRequest(BaseModel):
    email: str
    pin: str
    
    _validate_email = field_validator('email')(validate_email)
    
class Resend2FARequest(BaseModel):
    email: str
    
    _validate_email = field_validator('email')(validate_email)
    
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    
class UserUpdate(BaseModel):
    nombre: str
    apellido: str
    email: str

    class Config:
        from_attributes = True
        
    _validate_email = field_validator('email')(validate_email)
        
class AdminUserUpdate(BaseModel):
    nombre: str
    apellido: str
    email: str
    estado_id: int
    rol_id: int

    class Config:
        from_attributes = True
        
    _validate_email = field_validator('email')(validate_email)

class PasswordRecoveryRequest(BaseModel):
    email: str
    
    _validate_email = field_validator('email')(validate_email)

class PinConfirmationRequest(BaseModel):
    email: str
    pin: str
    
    _validate_email = field_validator('email')(validate_email)

class PasswordResetRequest(BaseModel):
    email: str
    new_password: str
    
    _validate_email = field_validator('email')(validate_email)
    _validate_password = field_validator('new_password')(validate_password)