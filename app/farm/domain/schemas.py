from pydantic import BaseModel, ConfigDict, Field, field_validator
from decimal import Decimal
from typing import List
from app.infrastructure.utils.validators import validate_email_format, validate_no_emojis, validate_no_special_chars, validate_no_xss
from app.user.domain.schemas import UserForFarmResponse

class FarmCreate(BaseModel):
    """Schema para la creación de una nueva finca.

    Attributes:
        nombre (str): Nombre de la finca. Debe tener entre 2 y 100 caracteres.
        ubicacion (str): Ubicación de la finca. Debe tener entre 2 y 255 caracteres.
        area_total (Decimal): Área total de la finca. Debe ser mayor que 0.
        unidad_area_id (int): ID de la unidad de medida del área.
    """
    nombre: str = Field(..., min_length=2, max_length=100)
    ubicacion: str = Field(..., min_length=2, max_length=255)
    area_total: Decimal = Field(..., gt=0)
    unidad_area_id: int
    
    @field_validator('nombre')
    def validate_no_emojis_nombre(cls, v) -> str:
        """Valida que el nombre no contenga emojis.

        Args:
            v (str): Valor del nombre a validar.

        Returns:
            str: El valor validado.

        Raises:
            ValueError: Si el nombre contiene emojis.
        """
        return validate_no_emojis(v)
    
    @field_validator('nombre')
    def validate_no_special_chars_nombre(cls, v):
        return validate_no_special_chars(v)
    
    @field_validator('nombre')
    def validate_no_xss_nombre(cls, v):
        return validate_no_xss(v)
    
    @field_validator('ubicacion')
    def validate_no_emojis_ubicacion(cls, v):
        return validate_no_emojis(v)
    
    @field_validator('ubicacion')
    def validate_no_special_chars_ubicacion(cls, v):
        return validate_no_special_chars(v)
    
    @field_validator('ubicacion')
    def validate_no_xss_ubicacion(cls, v):
        return validate_no_xss(v)

    def to_log_dict(self) -> dict:
        """Convierte el modelo a un diccionario serializable para logs."""
        data = self.model_dump()
        data['area_total'] = float(data['area_total'])
        return data

class FarmResponse(BaseModel):
    """Schema para la respuesta con información de una finca.

    Attributes:
        id (int): Identificador único de la finca.
        nombre (str): Nombre de la finca.
        ubicacion (str): Ubicación de la finca.
        area_total (float): Área total de la finca.
        unidad_area (str): Unidad de medida del área.
        usuarios (List[UserForFarmResponse]): Lista de usuarios asociados a la finca.
    """
    id: int
    nombre: str
    ubicacion: str
    area_total: float
    unidad_area: str
    usuarios: List[UserForFarmResponse]

    model_config = ConfigDict(from_attributes=True)
    
class WorkerFarmResponse(BaseModel):
    """Schema para la respuesta con información de una finca.

    Attributes:
        id (int): Identificador único de la finca.
        nombre (str): Nombre de la finca.
        ubicacion (str): Ubicación de la finca.
    """
    id: int
    nombre: str
    ubicacion: str

    model_config = ConfigDict(from_attributes=True)
    
class PaginatedFarmListResponse(BaseModel):
    """Schema para la respuesta paginada de lista de fincas.

    Attributes:
        farms (List[FarmResponse]): Lista de fincas para la página actual.
        total_farms (int): Número total de fincas.
        page (int): Número de página actual (mínimo 1).
        per_page (int): Cantidad de elementos por página (entre 1 y 100).
        total_pages (int): Número total de páginas.
    """
    farms: List[FarmResponse]
    total_farms: int
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1, le=100)
    total_pages: int
    
class FarmUserAssignmentByEmail(BaseModel):
    """Schema para asignar usuarios a una finca mediante correos electrónicos.

    Attributes:
        farm_id (int): ID de la finca a la que se asignarán los usuarios.
        user_emails (List[str]): Lista de correos electrónicos de los usuarios.
    """
    farm_id: int
    user_emails: List[str]
    
    @field_validator('user_emails')
    def validate_emails(cls, emails) -> List[str]:
        """Valida el formato de todos los correos electrónicos en la lista.

        Args:
            emails (List[str]): Lista de correos electrónicos a validar.

        Returns:
            List[str]: Lista de correos electrónicos validados.

        Raises:
            ValueError: Si algún correo electrónico tiene un formato inválido.
        """
        validation_errors = []
        for email in emails:
            try:
                validate_email_format(email)
            except ValueError as e:
                validation_errors.append(f"Email '{email}': {str(e)}")
        
        if validation_errors:
            raise ValueError(validation_errors)
        return emails

class PaginatedFarmUserListResponse(BaseModel):
    """Schema para la respuesta paginada de lista de usuarios de una finca.

    Attributes:
        users (List[UserForFarmResponse]): Lista de usuarios para la página actual.
        total_users (int): Número total de usuarios.
        page (int): Número de página actual (mínimo 1).
        per_page (int): Cantidad de elementos por página (entre 1 y 100).
        total_pages (int): Número total de páginas.
    """
    users: List[UserForFarmResponse]
    total_users: int
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1, le=100)
    total_pages: int
    
class PaginatedWorkerFarmListResponse(BaseModel):
    """Schema para la respuesta paginada de lista de fincas.

    Attributes:
        farms (List[FarmResponse]): Lista de fincas para la página actual.
        total_farms (int): Número total de fincas.
        page (int): Número de página actual (mínimo 1).
        per_page (int): Cantidad de elementos por página (entre 1 y 100).
        total_pages (int): Número total de páginas.
    """
    farms: List[WorkerFarmResponse]
    total_farms: int
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1, le=100)
    total_pages: int

class FarmListResponse(BaseModel):
    """Schema para la respuesta de lista de fincas sin paginar.

    Attributes:
        farms (List[FarmResponse]): Lista de todas las fincas.
        total_farms (int): Número total de fincas.
    """
    farms: List[FarmResponse]
    total_farms: int

class FarmTasksStatsResponse(BaseModel):
    """Schema para la respuesta con estadísticas de tareas de una finca.

    Attributes:
        total_tasks (int): Total de tareas asignadas en la finca.
        completed_tasks (int): Total de tareas completadas en la finca.
        completion_rate (float): Porcentaje de tareas completadas.
    """
    total_tasks: int
    completed_tasks: int
    completion_rate: float
