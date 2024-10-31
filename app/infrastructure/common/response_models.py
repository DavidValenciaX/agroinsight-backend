from typing import List
from pydantic import BaseModel

class SuccessResponse(BaseModel):
    """
    Modelo de respuesta para operaciones exitosas.

    Attributes:
        message (str): Mensaje descriptivo del éxito de la operación.
    """
    message: str
    
class MultipleResponse(BaseModel):
    """
    Modelo de respuesta para operaciones que afectan a múltiples elementos.

    Attributes:
        messages (List[str]): Lista de mensajes descriptivos para cada elemento procesado.
        status_code (int): Código de estado HTTP de la respuesta.
    """
    messages: List[str]
    status_code: int
