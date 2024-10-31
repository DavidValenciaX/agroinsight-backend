import secrets
import hashlib

def generate_pin(length=4):
    """
    Genera un PIN aleatorio y su hash correspondiente.

    Args:
        length (int): Longitud del PIN a generar. Por defecto es 4.

    Returns:
        tuple: Un tuple que contiene el PIN generado y su hash.
    """
    pin = ''.join(secrets.choice('0123456789') for _ in range(length))
    pin_hash = hashlib.sha256(pin.encode()).hexdigest()
    return pin, pin_hash

def hash_pin(pin: str) -> str:
    """
    Calcula el hash SHA-256 de un PIN dado.

    Args:
        pin (str): El PIN a hashear.

    Returns:
        str: El hash SHA-256 del PIN.
    """
    return hashlib.sha256(pin.encode()).hexdigest()