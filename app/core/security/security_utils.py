from passlib.context import CryptContext

# Configurar el contexto de encriptación con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt. If the password is already hashed, it returns the password as is.
    """
    if not password.startswith("$2b$"):  # Asumiendo que usas bcrypt para hashing
        return pwd_context.hash(password)
    return password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)
