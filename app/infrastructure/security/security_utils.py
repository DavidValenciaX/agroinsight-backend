from passlib.context import CryptContext
from jose import jwt
from app.infrastructure.common.datetime_utils import datetime_utc_time
from app.infrastructure.config.settings import SECRET_KEY, ALGORITHM
from datetime import timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hashea una contraseña utilizando el algoritmo bcrypt.

    Args:
        password (str): La contraseña en texto plano a hashear.

    Returns:
        str: La contraseña hasheada.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con una contraseña hasheada.

    Args:
        plain_password (str): La contraseña en texto plano a verificar.
        hashed_password (str): La contraseña hasheada con la que se va a comparar.

    Returns:
        bool: True si la contraseña coincide, False en caso contrario.
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Crea un token de acceso JWT.

    Args:
        data (dict): Los datos que se incluirán en el token.
        expires_delta (timedelta, optional): Tiempo adicional para la expiración del token. 
            Si no se proporciona, el token expirará en 120 minutos.

    Returns:
        str: El token de acceso JWT codificado.
    """
    access_token_expire_minutes = 240
    to_encode = data.copy()
    
    current_time = datetime_utc_time()
    
    if expires_delta:
        expire = current_time + expires_delta
    else:
        expire = current_time + timedelta(minutes=access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
