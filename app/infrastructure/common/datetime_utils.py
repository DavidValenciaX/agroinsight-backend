from datetime import datetime, timezone
from sqlalchemy import func

def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        # Si el datetime es "naive" (sin zona horaria), asigna UTC
        return dt.replace(tzinfo=timezone.utc)
    # Si ya tiene zona horaria, devuélvelo tal como está
    return dt

def datetime_utc_time() -> datetime:
    # Obtener la hora actual en UTC directamente
    return datetime.now(timezone.utc)

def get_current_date() -> datetime.date:
    return datetime_utc_time().date()

def db_utc_time() -> datetime:
    """
    Obtiene la hora UTC directamente desde la base de datos PostgreSQL.
    
    El propósito principal es garantizar que se trabaje con una referencia de tiempo consistente y confiable, 
    sin depender de la configuración local del servidor o posibles desajustes de zona horaria. Utilizando 
    este método se asegura que todas las operaciones relacionadas con tiempo se basen en la misma fuente de verdad (la base de datos), 
    evitando así discrepancias temporales que podrían afectar el comportamiento de la aplicación.

    Returns:
        datetime: Tiempo UTC actual obtenido de la base de datos.
    """

    utc_time = func.timezone('UTC', func.current_timestamp()) # Obtener el valor del primer resultado
    return utc_time

