from sqlalchemy.orm import Session
from app.farm.application.services.farm_service import FarmService
from app.farm.infrastructure.sql_repository import FarmRepository
from app.farm.domain.schemas import FarmCreate
from app.infrastructure.common.response_models import SuccessResponse
from app.user.application.services.user_service import UserService
from app.user.domain.schemas import UserInDB
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

from app.user.infrastructure.sql_repository import UserRepository

class CreateFarmUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.farm_repository = FarmRepository(db)
        self.user_repository = UserRepository(db)
        self.user_service = UserService(db)
        self.farm_service = FarmService(db)

    def create_farm(self, farm_data: FarmCreate, current_user: UserInDB) -> SuccessResponse:
        
        # Validar que la unidad de medida exista
        unit_of_measure = self.farm_repository.get_unit_of_measure_by_id(farm_data.unidad_area_id)
        if not unit_of_measure:
            raise DomainException(
                message="La unidad de medida no existe.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Validar que la unidad de medida sea de area
        if self.farm_repository.get_unit_category_by_id(unit_of_measure.categoria_id).nombre != self.farm_service.UNIT_CATEGORY_AREA_NAME:
            raise DomainException(
                message="La unidad de medida no es de área.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        existing_farm = self.farm_repository.get_farm_by_name(farm_data.nombre)
        
        if existing_farm:
            if self.farm_service.user_is_farm_admin(current_user.id, existing_farm.id):
                raise DomainException(
                    message="El usuario ya tiene una finca registrada con ese nombre. Por favor, escoja un nombre diferente.",
                    status_code=status.HTTP_409_CONFLICT
                )

        # Crear la finca
        farm = self.farm_repository.create_farm(farm_data)
        if not farm:
            raise DomainException(
                message="No se pudo crear la finca.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        admin_role = self.farm_service.get_admin_role()
        
        # Asignar el rol de administrador a la finca
        self.farm_repository.add_user_to_farm_with_role(current_user.id, farm.id, admin_role.id)

        return SuccessResponse(message="Finca creada exitosamente")
