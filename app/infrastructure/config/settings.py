"""
Módulo de configuración de la aplicación.

Este módulo carga las variables de entorno necesarias para la configuración
de la aplicación, como claves secretas y algoritmos de seguridad.
"""

from dotenv import load_dotenv
import os

load_dotenv(override=True)

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')
WARNING_TIME = int(os.getenv('WARNING_TIME', 1))
DEFAULT_EXPIRATION_TIME = int(os.getenv('DEFAULT_EXPIRATION_TIME', 10))

def get_settings() -> dict:
    """
    Obtiene la configuración de la aplicación desde las variables de entorno.

    Returns:
        dict: Un diccionario con las configuraciones de la aplicación, que incluye:
            - SECRET_KEY: Clave secreta para la aplicación.
            - ALGORITHM: Algoritmo utilizado para la codificación.
            - WARNING_TIME: Tiempo de advertencia en minutos.
            - DEFAULT_EXPIRATION_TIME: Tiempo de expiración por defecto en minutos.
    """
    return {
        "SECRET_KEY": SECRET_KEY,
        "ALGORITHM": ALGORITHM,
        "WARNING_TIME": WARNING_TIME,
        "DEFAULT_EXPIRATION_TIME": DEFAULT_EXPIRATION_TIME
    }