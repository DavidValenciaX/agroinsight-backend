from sqlalchemy.orm import Session
from typing import List
from app.logs.domain.schemas import ActivityLogResponse
from app.logs.infrastructure.sql_repository import LogRepository
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class GetPaginatedLogsUseCase:
    """
    Caso de uso para obtener logs paginados del sistema.

    Esta clase maneja la lógica de negocio para recuperar logs de actividad
    del sistema de manera paginada.

    Attributes:
        db (Session): Sesión de base de datos para realizar operaciones.
        log_repository (LogRepository): Repositorio para operaciones relacionadas con logs.
    """

    def __init__(self, db: Session):
        """
        Inicializa una nueva instancia de GetPaginatedLogsUseCase.

        Args:
            db (Session): Sesión de base de datos para operaciones de persistencia.
        """
        self.db = db
        self.log_repository = LogRepository(db)

    def get_logs(self, page: int = 1, limit: int = 100) -> List[ActivityLogResponse]:
        """
        Obtiene una lista paginada de logs del sistema.

        Args:
            page (int): Número de página a recuperar (comienza en 1).
            limit (int): Cantidad de registros por página.

        Returns:
            List[ActivityLogResponse]: Lista de logs de actividad.

        Raises:
            DomainException: Si ocurre un error al recuperar los logs.
        """
        try:
            offset = (page - 1) * limit
            logs = self.log_repository.get_paginated_logs(limit=limit, offset=offset)
            return logs
        except Exception as e:
            raise DomainException(
                message=f"Error al obtener los logs del sistema: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 