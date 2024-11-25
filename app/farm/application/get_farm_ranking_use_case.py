from datetime import date
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.farm.domain.schemas import FarmRankingType, FarmRankingListResponse, FarmRankingResponse
from app.farm.infrastructure.sql_repository import FarmRepository
from app.farm.application.services.farm_service import FarmService
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class GetFarmRankingUseCase:
    """Caso de uso para obtener el ranking de fincas.
    
    Esta clase maneja la lógica de negocio para obtener un ranking de fincas
    basado en ganancias o producción dentro de un período específico.
    """

    def __init__(self, db: Session):
        """Inicializa el caso de uso con las dependencias necesarias."""
        self.db = db
        self.farm_repository = FarmRepository(db)
        self.farm_service = FarmService(db)

    def get_farm_ranking(
        self,
        current_user: UserInDB,
        ranking_type: FarmRankingType,
        limit: int = 10,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> FarmRankingListResponse:
        """Obtiene el ranking de fincas según el criterio especificado.

        Args:
            current_user (UserInDB): Usuario actual
            ranking_type (FarmRankingType): Tipo de ranking (PROFIT/PRODUCTION)
            limit (int): Cantidad máxima de fincas a retornar
            start_date (Optional[date]): Fecha inicial del período
            end_date (Optional[date]): Fecha final del período

        Returns:
            FarmRankingListResponse: Lista de fincas rankeadas

        Raises:
            DomainException: Si ocurre algún error en la obtención del ranking
        """
        try:
            # Obtener el rol de administrador
            admin_role = self.farm_service.get_admin_role()

            # Obtener las fincas rankeadas según el tipo
            if ranking_type == FarmRankingType.PROFIT:
                ranked_farms = self.farm_repository.get_farms_ranked_by_profit(
                    current_user.id,
                    admin_role.id,
                    limit,
                    start_date,
                    end_date
                )
            else:  # PRODUCTION
                ranked_farms = self.farm_repository.get_farms_ranked_by_production(
                    current_user.id,
                    admin_role.id,
                    limit,
                    start_date,
                    end_date
                )

            # Construir la respuesta
            farm_responses = [
                FarmRankingResponse(
                    farm_id=farm.id,
                    farm_name=farm.nombre,
                    value=value,
                    ranking_position=position + 1
                )
                for position, (farm, value) in enumerate(ranked_farms)
            ]

            return FarmRankingListResponse(
                farms=farm_responses,
                total_farms=len(farm_responses),
                ranking_type=ranking_type,
                start_date=start_date,
                end_date=end_date
            )

        except Exception as e:
            raise DomainException(
                message=f"Error al obtener el ranking de fincas: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 