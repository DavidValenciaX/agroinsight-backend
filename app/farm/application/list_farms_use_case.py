from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.farm.domain.schemas import FarmListResponse, FarmResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class ListFarmsUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.farm_repository = FarmRepository(db)

    def execute(self, current_user: UserInDB) -> FarmListResponse:
        # Verificar si el usuario tiene permisos para listar fincas
        if not self.user_can_list_farms(current_user):
            raise DomainException(
                message="No tienes permisos para listar fincas.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Obtener las fincas del repositorio
        farms = self.farm_repository.list_farms(current_user.id)

        # Construir y retornar la respuesta
        farm_responses = [
            FarmResponse(
                id=farm.id,
                nombre=farm.nombre,
                ubicacion=farm.ubicacion,
                area_total=farm.area_total,
                unidad_area=farm.unidad_area.abreviatura,
                latitud=farm.latitud,
                longitud=farm.longitud
            ) for farm in farms
        ]

        return FarmListResponse(farms=farm_responses)

    def user_can_list_farms(self, user: UserInDB) -> bool:
        # Implementar la lógica para verificar si el usuario puede listar fincas
        # Por ejemplo, verificar si tiene un rol específico
        allowed_roles = ["Superusuario", "Administrador de finca", "Usuario"]
        return any(role.nombre in allowed_roles for role in user.roles)