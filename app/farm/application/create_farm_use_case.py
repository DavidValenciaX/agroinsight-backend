from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FarmRepository
from app.farm.domain.schemas import FarmCreate
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class CreateFarmUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.farm_repository = FarmRepository(db)

    def create_farm(self, farm_data: FarmCreate, current_user: UserInDB) -> SuccessResponse:
        
        # Validar los datos de entrada
        self.validate_farm_data(farm_data)
        
        # Verificar si ya existe una finca con el mismo nombre para este usuario
        if self.farm_repository.farm_exists_for_user(current_user.id, farm_data.nombre):
            raise DomainException(
                message="El usuario ya tiene una finca registrada con ese nombre. Por favor, escoja un nombre diferente.",
                status_code=status.HTTP_409_CONFLICT
            )

        # Crear la finca
        farm = self.farm_repository.create_farm(farm_data, current_user.id)
        if not farm:
            raise DomainException(
                message="No se pudo crear la finca.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return SuccessResponse(message="Finca creada exitosamente")

    def validate_farm_data(self, farm_data: FarmCreate):
        # Implementar validaciones adicionales si es necesario
        if farm_data.area_total <= 0:
            raise DomainException(
                message="El área total debe ser mayor que cero.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        # Agregar más validaciones según sea necesario