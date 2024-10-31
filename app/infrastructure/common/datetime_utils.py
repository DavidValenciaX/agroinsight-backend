from datetime import datetime, timezone
from sqlalchemy import func

def ensure_utc(dt: datetime) -> datetime:
    """
    Asegura que un objeto datetime tenga zona horaria UTC.

    Args:
        dt (datetime): Objeto datetime a convertir.

    Returns:
        datetime: Objeto datetime con zona horaria UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

def datetime_utc_time() -> datetime:
    """
    Obtiene la hora actual en UTC.

    Returns:
        datetime: Hora actual en UTC.
    """
    return datetime.now(timezone.utc)

def get_current_date() -> datetime.date:
    """
    Obtiene la fecha actual en UTC.

    Returns:
        datetime.date: Fecha actual en UTC.
    """
    return datetime_utc_time().date()

def db_utc_time() -> datetime:
    """
    Obtiene una expresión SQL para la hora actual en UTC.

    Returns:
        datetime: Expresión SQL para la hora actual en UTC.
    """
    utc_time = func.timezone('UTC', func.current_timestamp())
    return utc_time

