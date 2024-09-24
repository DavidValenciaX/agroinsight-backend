from typing import List
from datetime import datetime
from pydantic import BaseModel, field_validator
from pydantic_core import PydanticCustomError
import re

class UserCreate(BaseModel):
    email: str
    nombre: str
    apellido: str
    password: str
    
    @field_validator('email')
    def validate_email(cls, v):
        # Expresión regular básica para validar el formato del correo electrónico
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, v):
            raise PydanticCustomError('email_validation','El correo electrónico no es válido. Debe contener un @ y un dominio válido.')
        return v

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

    @field_validator('password')
    def validate_password(cls, v):
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
            # Unir los errores en un solo mensaje
            message = '\n'.join(errors)
            # Levantar un error personalizado sin prefijo
            raise PydanticCustomError('password_validation', message)
        return v


class UserCreationResponse(BaseModel):
    message: str
    user_state: str

class ResendPinConfirmRequest(BaseModel):
    email: str
    
    @field_validator('email')
    def validate_email(cls, v):
        # Expresión regular básica para validar el formato del correo electrónico
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, v):
            raise PydanticCustomError('email_validation','El correo electrónico no es válido. Debe contener un @ y un dominio válido.')
        return v
    
class ResendConfirmationResponse(BaseModel):
    message: str

class ConfirmationRequest(BaseModel):
    email: str
    pin: str
    
    @field_validator('email')
    def validate_email(cls, v):
        # Expresión regular básica para validar el formato del correo electrónico
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, v):
            raise PydanticCustomError('email_validation','El correo electrónico no es válido. Debe contener un @ y un dominio válido.')
        return v
    
class ConfirmUsuarioResponse(BaseModel):
    message: str

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
        
    @field_validator('email')
    def validate_email(cls, v):
        # Expresión regular básica para validar el formato del correo electrónico
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, v):
            raise PydanticCustomError('email_validation','El correo electrónico no es válido. Debe contener un @ y un dominio válido.')
        return v

class UserResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str
    estado: str
    rol: str

    class Config:
        from_attributes = True

    @field_validator('email')
    def validate_email(cls, v):
        # Expresión regular básica para validar el formato del correo electrónico
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, v):
            raise PydanticCustomError('email_validation','El correo electrónico no es válido. Debe contener un @ y un dominio válido.')
        return v

class LoginRequest(BaseModel):
    email: str
    password: str
    
    @field_validator('email')
    def validate_email(cls, v):
        # Expresión regular básica para validar el formato del correo electrónico
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, v):
            raise PydanticCustomError('email_validation','El correo electrónico no es válido. Debe contener un @ y un dominio válido.')
        return v
    
class LoginResponse(BaseModel):
    message: str
    user_state: str
    
class TwoFactorAuthRequest(BaseModel):
    email: str
    pin: str
    
    @field_validator('email')
    def validate_email(cls, v):
        # Expresión regular básica para validar el formato del correo electrónico
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, v):
            raise PydanticCustomError('email_validation','El correo electrónico no es válido. Debe contener un @ y un dominio válido.')
        return v
    
class Resend2FARequest(BaseModel):
    email: str
    
    @field_validator('email')
    def validate_email(cls, v):
        # Expresión regular básica para validar el formato del correo electrónico
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, v):
            raise PydanticCustomError('email_validation','El correo electrónico no es válido. Debe contener un @ y un dominio válido.')
        return v
    
class Resend2FAResponse(BaseModel):
    message: str
    
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    
class UserUpdate(BaseModel):
    nombre: str
    apellido: str
    email: str

    class Config:
        from_attributes = True
        
    @field_validator('email')
    def validate_email(cls, v):
        # Expresión regular básica para validar el formato del correo electrónico
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, v):
            raise PydanticCustomError('email_validation','El correo electrónico no es válido. Debe contener un @ y un dominio válido.')
        return v
        
class AdminUserUpdate(BaseModel):
    nombre: str
    apellido: str
    email: str
    estado_id: int
    rol_id: int

    class Config:
        from_attributes = True
        
    @field_validator('email')
    def validate_email(cls, v):
        # Expresión regular básica para validar el formato del correo electrónico
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, v):
            raise PydanticCustomError('email_validation','El correo electrónico no es válido. Debe contener un @ y un dominio válido.')
        return v

class PasswordRecoveryRequest(BaseModel):
    email: str
    
    @field_validator('email')
    def validate_email(cls, v):
        # Expresión regular básica para validar el formato del correo electrónico
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, v):
            raise PydanticCustomError('email_validation','El correo electrónico no es válido. Debe contener un @ y un dominio válido.')
        return v

class PasswordRecoveryResponse(BaseModel):
    message: str
    
class ResendRecoveryResponse(BaseModel):
    message: str

class PinConfirmationRequest(BaseModel):
    email: str
    pin: str
    
    @field_validator('email')
    def validate_email(cls, v):
        # Expresión regular básica para validar el formato del correo electrónico
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, v):
            raise PydanticCustomError('email_validation','El correo electrónico no es válido. Debe contener un @ y un dominio válido.')
        return v
    
class ConfirmRecoveryResponse(BaseModel):
    message: str

class PasswordResetRequest(BaseModel):
    email: str
    new_password: str
    
    @field_validator('email')
    def validate_email(cls, v):
        # Expresión regular básica para validar el formato del correo electrónico
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, v):
            raise PydanticCustomError('email_validation','El correo electrónico no es válido. Debe contener un @ y un dominio válido.')
        return v
    
    @field_validator('new_password')
    def validate_password(cls, v):
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
            # Unir los errores en un solo mensaje
            message = '\n'.join(errors)
            # Levantar un error personalizado sin prefijo
            raise PydanticCustomError('password_validation', message)
        return v
    
class ResetPasswordResponse(BaseModel):
    message: str
