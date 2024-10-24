import re
from pydantic_core import PydanticCustomError
from typing import Optional

def validate_email_format(email: str) -> Optional[str]:
    """
    Valida el formato de una dirección de correo electrónico.

    Args:
        email (str): La dirección de correo electrónico a validar.

    Returns:
        str: La dirección de correo electrónico si es válida.

    Raises:
        ValueError: Si la dirección de correo electrónico no es válida.
    """
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, email):
        raise ValueError("El correo electrónico no es válido. Debe contener un @ y un dominio válido.")
    return email

# Mantener la función original para compatibilidad con el resto del código
def validate_email(v: str) -> str:
    """
    Wrapper para mantener compatibilidad con el código existente.
    """
    try:
        return validate_email_format(v)
    except ValueError as e:
        raise PydanticCustomError('email_validation', str(e))
