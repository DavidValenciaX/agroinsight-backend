from fastapi import Request
from app.infrastructure.db.connection import getDb
import logging

logger = logging.getLogger(__name__)

async def database_middleware(request: Request, call_next):
    """Middleware para inyectar la sesión de base de datos en cada request."""
    logger.info("Database middleware started")
    db = next(getDb())
    request.state.db = db
    try:
        response = await call_next(request)
        return response
    finally:
        db.close()