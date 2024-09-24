from sqlalchemy.orm import Session
from app.farm.infrastructure.sql_repository import FincaRepository
from app.farm.domain.schemas import FincaCreate, FincaResponse
from app.user.domain.schemas import UserInDB
from app.farm.domain.exceptions import DomainException
from fastapi import status

class CrearFincaUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.finca_repository = FincaRepository(db)

    def execute(self, finca_data: FincaCreate, current_user: UserInDB) -> FincaResponse:
        # Verificar si el usuario tiene permisos para crear fincas
        if not self.user_can_create_finca(current_user):
            raise DomainException(
                message="No tienes permisos para crear fincas.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Validar los datos de entrada
        self.validate_finca_data(finca_data)

        # Crear la finca
        finca = self.finca_repository.create_finca(finca_data, current_user.id)
        if not finca:
            raise DomainException(
                message="No se pudo crear la finca.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Construir y retornar la respuesta
        return FincaResponse(
            id=finca.id,
            nombre=finca.nombre,
            ubicacion=finca.ubicacion,
            area_total=finca.area_total,
            unidad_area=finca.unidad_area.abreviatura,
            latitud=finca.latitud,
            longitud=finca.longitud
        )

    def user_can_create_finca(self, user: UserInDB) -> bool:
        # Implementar la lógica para verificar si el usuario puede crear fincas
        # Por ejemplo, verificar si tiene un rol específico
        allowed_roles = ["Superusuario", "Administrador de finca"]
        return any(role.nombre in allowed_roles for role in user.roles)

    def validate_finca_data(self, finca_data: FincaCreate):
        # Implementar validaciones adicionales si es necesario
        if finca_data.area_total <= 0:
            raise DomainException(
                message="El área total debe ser mayor que cero.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        # Agregar más validaciones según sea necesario