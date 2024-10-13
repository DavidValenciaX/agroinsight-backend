from datetime import datetime, timezone
from app.infrastructure.db.connection import SessionLocal
from sqlalchemy import text

def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        # Si el datetime es "naive" (sin zona horaria), asigna UTC
        return dt.replace(tzinfo=timezone.utc)
    # Si ya tiene zona horaria, devuélvelo tal como está
    return dt

def datetime_timezone_utc_now() -> datetime:
    # Obtener la hora actual en UTC directamente
    return datetime.now(timezone.utc)

def get_current_date() -> datetime.date:
    return datetime_timezone_utc_now().date()

def get_db_utc_time() -> datetime:
    """
    Obtiene la hora UTC directamente desde la base de datos PostgreSQL.
    
    El propósito principal es garantizar que se trabaje con una referencia de tiempo consistente y confiable, 
    sin depender de la configuración local del servidor o posibles desajustes de zona horaria. Utilizando 
    este método se asegura que todas las operaciones relacionadas con tiempo se basen en la misma fuente de verdad (la base de datos), 
    evitando así discrepancias temporales que podrían afectar el comportamiento de la aplicación.

    Returns:
        datetime: Tiempo UTC actual obtenido de la base de datos.
    """
    # Crear la sesión manualmente
    session = SessionLocal()
    try:
        # Consulta para obtener el tiempo en UTC desde la base de datos
        result = session.execute(text("SELECT current_timestamp AT TIME ZONE 'UTC' AS utc_time"))
        utc_time = result.scalar()  # Obtener el valor del primer resultado
        return utc_time
    finally:
        session.close()  
