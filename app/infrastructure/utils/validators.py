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

def validate_no_emojis(text: str) -> str:
    """
    Valida que el texto no contenga emojis.
    
    Args:
        text (str): Texto a validar
        
    Returns:
        str: El texto validado
        
    Raises:
        ValueError: Si el texto contiene emojis
    """
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # símbolos & pictogramas
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # banderas (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    
    if emoji_pattern.search(text):
        raise ValueError("El texto no puede contener emojis, símbolos o pictogramas.")
    return text
