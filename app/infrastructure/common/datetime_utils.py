from datetime import datetime, timezone

def ensure_utc(dt: datetime) -> datetime:
    """
    Asegura que un objeto datetime tenga zona horaria UTC.
    Si ya tiene zona horaria, lo devuelve tal cual.
    Si no tiene zona horaria, le asigna UTC.
    
    Parameters:
    dt (datetime): El datetime a verificar y ajustar.
    
    Returns:
    datetime: El datetime con zona horaria UTC.
    """
    if dt.tzinfo is None:
        # Si el datetime es "naive" (sin zona horaria), asigna UTC
        return dt.replace(tzinfo=timezone.utc)
    # Si ya tiene zona horaria, devuélvelo tal como está
    return dt
