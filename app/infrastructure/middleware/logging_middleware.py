from fastapi import Request
from sqlalchemy.orm import Session
from app.logs.infrastructure.sql_repository import LogRepository
from app.logs.application.services.log_service import LogService

async def logging_middleware(request: Request, call_next):
    # Obtener la sesión de base de datos
    db: Session = request.state.db
    
    # Crear el repositorio y servicio de logs
    log_repository = LogRepository(db)
    log_service = LogService(log_repository)
    
    # Inyectar el servicio en el request
    request.state.log_service = log_service
    
    # Continuar con el request
    response = await call_next(request)
    return response 