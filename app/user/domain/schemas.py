import re
from typing import List, Optional
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
    """
    Esquema para crear un nuevo usuario.

    Atributos:
    ---------
        - nombre (str): Nombre del usuario.
        - apellido (str): Apellido del usuario.
        - email (EmailStr): Correo electrónico único del usuario.
        - password (str): Contraseña del usuario.
    """
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
    """
    Esquema para solicitar el reenvío del PIN de confirmación.

    Atributos:
    ---------
        - email (EmailStr): Correo electrónico del usuario.
    """
    email: str
    
    _validate_email = field_validator('email')(validate_email)

class ConfirmationRequest(BaseModel):
    """
    Esquema para confirmar el registro de un usuario mediante PIN.

    Atributos:
    ---------
        - email (EmailStr): Correo electrónico del usuario.
        - pin (str): PIN de confirmación enviado al correo.
    """
    email: str
    pin: str
    
    _validate_email = field_validator('email')(validate_email)

class UserCreateByAdmin(UserCreate):
    """
    Esquema para que un administrador cree un nuevo usuario.

    Atributos:
    ---------
        - nombre (str): Nombre del usuario.
        - apellido (str): Apellido del usuario.
        - email (EmailStr): Correo electrónico único del usuario.
        - password (str): Contraseña del usuario.
        - roles (List[int]): Lista de IDs de roles asignados al usuario.
        - finca_id (int): ID de la finca a la que pertenece el usuario.
    """
    role_id: int
    finca_id: int

class RoleInfo(BaseModel):
    """
    Esquema que representa la información de un rol.

    Atributos:
    ---------
        - id (int): Identificador único del rol.
        - nombre (str): Nombre del rol.
    """
    id: int
    nombre: str

class UserInDB(BaseModel):
    """
    Esquema que representa al usuario almacenado en la base de datos.

    Atributos:
    ---------
        - id (int): Identificador único del usuario.
        - nombre (str): Nombre del usuario.
        - apellido (str): Apellido del usuario.
        - email (EmailStr): Correo electrónico único del usuario.
        - roles (List[str]): Lista de nombres de roles asignados al usuario.
        - estado (str): Estado actual del usuario.
    """
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

class RolFinca(BaseModel):
    rol: str
    finca: Optional[str]

class UserResponse(BaseModel):
    """
    Esquema para la respuesta que contiene información del usuario.

    Atributos:
    ---------
        - id (int): Identificador único del usuario.
        - nombre (str): Nombre del usuario.
        - apellido (str): Apellido del usuario.
        - email (EmailStr): Correo electrónico único del usuario.
        - roles (List[str]): Lista de nombres de roles asignados al usuario.
        - estado (str): Estado actual del usuario.
    """
    id: int
    nombre: str
    apellido: str
    email: str
    estado: str
    roles_fincas: List[RolFinca]  # Updated to include farm names

    class Config:
        from_attributes = True

    _validate_email = field_validator('email')(validate_email)

class LoginRequest(BaseModel):
    """
    Esquema para solicitar un inicio de sesión.

    Atributos:
    ---------
        - email (EmailStr): Correo electrónico del usuario.
        - password (str): Contraseña del usuario.
    """
    email: str
    password: str
    
    _validate_email = field_validator('email')(validate_email)
    _validate_password = field_validator('password')(validate_password)
    
class TwoFactorAuthRequest(BaseModel):
    """
    Esquema para verificar el inicio de sesión con autenticación de dos factores.

    Atributos:
    ---------
        - email (EmailStr): Correo electrónico del usuario.
        - pin (str): PIN de autenticación de dos factores.
    """
    email: str
    pin: str
    
    _validate_email = field_validator('email')(validate_email)
    
class Resend2FARequest(BaseModel):
    """
    Esquema para solicitar el reenvío del PIN de autenticación de dos factores.

    Atributos:
    ---------
        - email (EmailStr): Correo electrónico del usuario.
    """
    email: str
    
    _validate_email = field_validator('email')(validate_email)
    
class TokenResponse(BaseModel):
    """
    Esquema para la respuesta que contiene el token de acceso.

    Atributos:
    ---------
        - access_token (str): Token de acceso JWT.
        - token_type (str): Tipo de token, generalmente "bearer".
    """
    access_token: str
    token_type: str
    
class UserUpdate(BaseModel):
    """
    Esquema para actualizar la información del usuario actual.

    Atributos:
    ---------
        - nombre (Optional[str]): Nuevo nombre del usuario.
        - apellido (Optional[str]): Nuevo apellido del usuario.
        - password (Optional[str]): Nueva contraseña del usuario.
    """
    nombre: str
    apellido: str
    email: str

    class Config:
        from_attributes = True
        
    _validate_email = field_validator('email')(validate_email)
        
class AdminUserUpdate(BaseModel):
    """
    Esquema para que un administrador actualice la información de un usuario específico.

    Atributos:
    ---------
        - nombre (Optional[str]): Nuevo nombre del usuario.
        - apellido (Optional[str]): Nuevo apellido del usuario.
        - email (Optional[EmailStr]): Nuevo correo electrónico del usuario.
        - roles (Optional[List[int]]): Nueva lista de IDs de roles asignados al usuario.
        - estado_id (Optional[int]): Nuevo ID de estado del usuario.
        - finca_id (Optional[int]): Nuevo ID de finca del usuario.
    """
    nombre: str
    apellido: str
    email: str
    estado_id: int
    rol_id: int
    finca_id: int

    class Config:
        from_attributes = True
        
    _validate_email = field_validator('email')(validate_email)

class PasswordRecoveryRequest(BaseModel):
    """
    Esquema para iniciar el proceso de recuperación de contraseña.

    Atributos:
    ---------
        - email (EmailStr): Correo electrónico del usuario.
    """
    email: str
    
    _validate_email = field_validator('email')(validate_email)

class PinConfirmationRequest(BaseModel):
    """
    Esquema para confirmar el PIN de recuperación de contraseña.

    Atributos:
    ---------
        - email (EmailStr): Correo electrónico del usuario.
        - pin (str): PIN de recuperación enviado al correo.
    """
    email: str
    pin: str
    
    _validate_email = field_validator('email')(validate_email)

class PasswordResetRequest(BaseModel):
    """
    Esquema para restablecer la contraseña del usuario.

    Atributos:
    ---------
        - email (EmailStr): Correo electrónico del usuario.
        - new_password (str): Nueva contraseña del usuario.
    """
    email: str
    new_password: str
    
    _validate_email = field_validator('email')(validate_email)
    _validate_password = field_validator('new_password')(validate_password)