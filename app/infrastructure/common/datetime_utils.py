from datetime import datetime, timezone
from sqlalchemy import func

def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

def datetime_utc_time() -> datetime:
    return datetime.now(timezone.utc)

def get_current_date() -> datetime.date:
    return datetime_utc_time().date()

def db_utc_time() -> datetime:
    utc_time = func.timezone('UTC', func.current_timestamp())
    return utc_time

