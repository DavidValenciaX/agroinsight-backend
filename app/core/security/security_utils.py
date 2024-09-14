from passlib.context import CryptContext
import re

# Configurar el contexto de encriptación con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def validate_password(password: str) -> str:
    errors = []
    if len(password) < 12:
        errors.append('La contraseña debe tener al menos 12 caracteres')
    if not re.search(r'\d', password):
        errors.append('La contraseña debe contener al menos un número')
    if not re.search(r'[a-zA-Z]', password):
        errors.append('La contraseña debe contener al menos una letra')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append('La contraseña debe contener al menos un caracter especial')
    
    if errors:
        raise ValueError(', '.join(errors))
    return password
