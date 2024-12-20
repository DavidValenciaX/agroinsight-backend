import re
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from pydantic_core import PydanticCustomError
from app.infrastructure.utils.validators import validate_email, validate_no_emojis, validate_no_special_chars, validate_no_xss
from zxcvbn import zxcvbn

def validate_password(v: str) -> str:
    """
    Valida la fortaleza de una contraseña con criterios avanzados.
    Acepta caracteres ASCII imprimibles [RFC20] y Unicode [ISO/ISC 10646].

    Args:
        v (str): La contraseña a validar.

    Returns:
        str: La contraseña validada.

    Raises:
        PydanticCustomError: Si la contraseña no cumple con los requisitos de seguridad.
    """
    errors = []
    
    # Validación de caracteres permitidos
    ascii_printable = set(range(32, 127))  # Caracteres ASCII imprimibles incluyendo espacio
    if not all(ord(char) in ascii_printable or ord(char) > 127 for char in v):
        errors.append('La contraseña solo puede contener caracteres ASCII imprimibles o Unicode válidos.')

    # Validaciones básicas de longitud (contando cada carácter Unicode como uno solo)
    if len(v) < 12:
        errors.append('La contraseña debe tener al menos 12 caracteres.')
    if len(v) > 64:
        errors.append('La contraseña no debe exceder los 64 caracteres.')

    # Validaciones de caracteres requeridos
    if not re.search(r'\d', v):
        errors.append('La contraseña debe contener al menos un número.')
    if not re.search(r'[A-Z]', v):
        errors.append('La contraseña debe contener al menos una letra mayúscula.')
    if not re.search(r'[a-z]', v):
        errors.append('La contraseña debe contener al menos una letra minúscula.')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
        errors.append('La contraseña debe contener al menos un carácter especial.')

    # Validación de patrones repetitivos
    if re.search(r'(.)\1{2,}', v):
        errors.append('La contraseña no debe contener caracteres repetidos más de 2 veces seguidas.')
    
    # Validación de secuencias comunes
    secuencias_comunes = [
        'qwerty', 'asdfgh', '123456', 'abcdef',
        'password', 'contraseña', 'admin123', '123abc'
    ]
    v_lower = v.lower()
    for secuencia in secuencias_comunes:
        if secuencia in v_lower:
            errors.append('La contraseña no debe contener secuencias comunes o predecibles.')
            break

    # Validación de patrones de teclado
    patrones_teclado = [
        'qwerty', 'asdfgh', 'zxcvbn', 'qazwsx',
        '123456', '098765'
    ]
    for patron in patrones_teclado:
        if patron in v_lower:
            errors.append('La contraseña no debe contener patrones de teclado.')
            break

    # Validación de entropía
    def calcular_entropia(password: str) -> float:
        # Calcula la entropía basada en la variedad de caracteres y su distribución
        char_count = {}
        for char in password:
            char_count[char] = char_count.get(char, 0) + 1
        
        entropia = len(set(password)) * len(password) / max(char_count.values())
        return entropia

    if calcular_entropia(v) < 30:  # El valor 30 es un ejemplo, ajustar según necesidades
        errors.append('La contraseña debe tener mayor variedad de caracteres y mejor distribución.')

    result = zxcvbn(v)
    if result['score'] < 3:  # scores van de 0 a 4
        errors.append(f'La contraseña es demasiado débil: {result["feedback"]["warning"]}')

    if errors:
        message = '\n'.join(errors)
        raise PydanticCustomError('password_validation', message)
    return v

class UserCreate(BaseModel):
    """
    Esquema para crear un nuevo usuario.

    Attributes:
        email (str): Correo electrónico del usuario.
        nombre (str): Nombre del usuario.
        apellido (str): Apellido del usuario.
        password (str): Contraseña del usuario.
    """
    email: str
    nombre: str = Field(..., min_length=2)
    apellido: str = Field(..., min_length=2)
    password: str
    acepta_terminos: bool = False
    
    @field_validator('acepta_terminos')
    def validate_terms_acceptance(cls, v):
        if not v:
            raise ValueError("Debes aceptar los términos y condiciones para registrarte")
        return v
    
    @field_validator('email')
    def validate_email(cls, v):
        return validate_email(v)
    
    @field_validator('password')
    def validate_password(cls, v):
        return validate_password(v)
    
    @field_validator('nombre')
    def validate_no_emojis_nombre(cls, v):
        return validate_no_emojis(v)
    
    @field_validator('nombre')
    def validate_no_special_chars_nombre(cls, v):
        return validate_no_special_chars(v)
    
    @field_validator('nombre')
    def validate_no_xss_nombre(cls, v):
        return validate_no_xss(v)
    
    @field_validator('apellido')
    def validate_no_emojis_apellido(cls, v):
        return validate_no_emojis(v)
    
    @field_validator('apellido')
    def validate_no_special_chars_apellido(cls, v):
        return validate_no_special_chars(v)
    
    @field_validator('apellido')
    def validate_no_xss_apellido(cls, v):
        return validate_no_xss(v)

class ResendPinConfirmRequest(BaseModel):
    """
    Esquema para solicitar el reenvío del PIN de confirmación.

    Attributes:
        email (str): Correo electrónico del usuario.
    """
    email: str
    
    @field_validator('email')
    def validate_email(cls, v):
        return validate_email(v)

class ConfirmationRequest(BaseModel):
    """
    Esquema para confirmar el registro de un usuario mediante PIN.

    Attributes:
        email (str): Correo electrónico del usuario.
        pin (str): PIN de confirmación enviado al correo.
    """
    email: str
    pin: str
    
    @field_validator('email')
    def validate_email(cls, v):
        return validate_email(v)
    
class RoleFarm(BaseModel):
    """
    Esquema que representa el rol y la finca de un usuario.

    Attributes:
        rol (str): Rol del usuario.
        finca (Optional[str]): Nombre de la finca (opcional).
    """
    rol: str
    finca: Optional[str]

class UserInDB(BaseModel):
    """
    Esquema que representa al usuario almacenado en la base de datos.

    Attributes:
        id (int): Identificador único del usuario.
        nombre (str): Nombre del usuario.
        apellido (str): Apellido del usuario.
        email (str): Correo electrónico único del usuario.
        password (str): Contraseña encriptada del usuario.
        failed_attempts (int): Número de intentos fallidos de inicio de sesión.
        locked_until (datetime): Fecha y hora hasta la que el usuario está bloqueado.
        state_id (int): Identificador del estado del usuario.
        roles_fincas (List[RoleFarm]): Lista de roles y fincas del usuario.
    """
    id: int
    nombre: str
    apellido: str
    email: str
    password: str
    failed_attempts: int
    locked_until: datetime
    state_id: int
    roles_fincas: List[RoleFarm]

    model_config = ConfigDict(from_attributes=True)
        
    @field_validator('email')
    def validate_email(cls, v):
        return validate_email(v)
    
    @field_validator('password')
    def validate_password(cls, v):
        return validate_password(v)

class UserResponse(BaseModel):
    """
    Esquema para la respuesta que contiene información del usuario.

    Attributes:
        id (int): Identificador único del usuario.
        nombre (str): Nombre del usuario.
        apellido (str): Apellido del usuario.
        email (str): Correo electrónico único del usuario.
        estado (str): Estado actual del usuario.
        roles_fincas (List[RoleFarm]): Lista de roles y fincas del usuario.
    """
    id: int
    nombre: str
    apellido: str
    email: EmailStr
    estado: str
    roles_fincas: List[RoleFarm]

    model_config = ConfigDict(from_attributes=True)
    
    
class UserForFarmResponse(BaseModel):
    """
    Esquema para la respuesta que contiene información de un usuario en el contexto de una finca.

    Attributes:
        id (int): Identificador único del usuario.
        nombre (str): Nombre del usuario.
        apellido (str): Apellido del usuario.
        email (EmailStr): Correo electrónico del usuario.
        estado (str): Estado actual del usuario.
        rol (str): Rol del usuario en la finca específica.
    """
    id: int
    nombre: str
    apellido: str
    email: EmailStr
    estado: str
    rol: str
    
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    """
    Esquema para solicitar un inicio de sesión.

    Attributes:
        email (str): Correo electrónico del usuario.
        password (str): Contraseña del usuario.
    """
    email: str
    password: str
    
    @field_validator('email')
    def validate_email(cls, v):
        return validate_email(v)
    
class TwoFactorAuthRequest(BaseModel):
    """
    Esquema para verificar el inicio de sesión con autenticación de dos factores.

    Attributes:
        email (str): Correo electrónico del usuario.
        pin (str): PIN de autenticación de dos factores.
    """
    email: str
    pin: str
    
    @field_validator('email')
    def validate_email(cls, v):
        return validate_email(v)
    
class Resend2FARequest(BaseModel):
    """
    Esquema para solicitar el reenvío del PIN de autenticación de dos factores.

    Attributes:
        email (str): Correo electrónico del usuario.
    """
    email: str
    
    @field_validator('email')
    def validate_email(cls, v):
        return validate_email(v)
    
class TokenResponse(BaseModel):
    """
    Esquema para la respuesta que contiene el token de acceso.

    Attributes:
        access_token (str): Token de acceso JWT.
        token_type (str): Tipo de token, generalmente "bearer".
    """
    access_token: str
    token_type: str
    
class UserUpdate(BaseModel):
    """
    Esquema para actualizar la información del usuario actual.

    Attributes:
        nombre (str): Nuevo nombre del usuario.
        apellido (str): Nuevo apellido del usuario.
        email (str): Nuevo correo electrónico del usuario.
    """
    nombre: str
    apellido: str
    email: str

    model_config = ConfigDict(from_attributes=True)
        
    @field_validator('email')
    def validate_email(cls, v):
        return validate_email(v)

class PasswordRecoveryRequest(BaseModel):
    """
    Esquema para iniciar el proceso de recuperación de contraseña.

    Attributes:
        email (str): Correo electrónico del usuario.
    """
    email: str
    
    @field_validator('email')
    def validate_email(cls, v):
        return validate_email(v)

class PinConfirmationRequest(BaseModel):
    """
    Esquema para confirmar el PIN de recuperación de contraseña.

    Attributes:
        email (str): Correo electrónico del usuario.
        pin (str): PIN de recuperación enviado al correo.
    """
    email: str
    pin: str
    
    @field_validator('email')
    def validate_email(cls, v):
        return validate_email(v)

class PasswordResetRequest(BaseModel):
    """
    Esquema para restablecer la contraseña del usuario.

    Attributes:
        email (str): Correo electrónico del usuario.
        new_password (str): Nueva contraseña del usuario.
    """
    email: str
    new_password: str
    
    @field_validator('email')
    def validate_email(cls, v):
        return validate_email(v)
    
    @field_validator('new_password')
    def validate_password(cls, v):
        return validate_password(v)

