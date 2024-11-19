from pydantic import BaseModel, ConfigDict, Field, field_validator
from decimal import Decimal
from typing import List, Type, Optional
from app.infrastructure.utils.validators import validate_no_emojis, validate_no_special_chars, validate_no_xss

class PlotCreate(BaseModel):
    """Schema para la creación de un nuevo lote.

    Este modelo define los datos necesarios para crear un lote en el sistema.

    Attributes:
        nombre (str): Nombre del lote. Debe tener entre 1 y 100 caracteres.
        area (Decimal): Área del lote. Debe ser un valor positivo.
        unidad_area_id (int): ID de la unidad de medida del área.
        latitud (Decimal): Latitud del lote. Debe estar entre -90 y 90.
        longitud (Decimal): Longitud del lote. Debe estar entre -180 y 180.
        finca_id (int): ID de la finca a la que pertenece el lote.
        costos_mantenimiento (Decimal): Costos de mantenimiento del lote. Debe ser un valor positivo.
        moneda_id (Optional[int]): ID de la moneda del lote. Opcional porque se asignará automáticamente.
    """
    nombre: str = Field(..., min_length=1, max_length=100)
    area: Decimal = Field(..., gt=0)
    unidad_area_id: int
    latitud: Decimal = Field(..., ge=-90, le=90)
    longitud: Decimal = Field(..., ge=-180, le=180)
    finca_id: int
    costos_mantenimiento: Decimal = Field(default=Decimal('0.00'), ge=0)
    moneda_id: Optional[int] = None
    
    @field_validator('nombre')
    def validate_no_emojis_nombre(cls: Type['PlotCreate'], v: str) -> str:
        """Valida que el nombre no contenga emojis.

        Args:
            cls: Clase del validador.
            v (str): Valor del nombre a validar.

        Returns:
            str: El valor validado.

        Raises:
            ValueError: Si el nombre contiene emojis.
        """
        return validate_no_emojis(v)
    
    @field_validator('nombre')
    def validate_no_special_chars_nombre(cls: Type['PlotCreate'], v: str) -> str:
        """Valida que el nombre no contenga caracteres especiales.

        Args:
            cls: Clase del validador.
            v (str): Valor del nombre a validar.

        Returns:
            str: El valor validado.

        Raises:
            ValueError: Si el nombre contiene caracteres especiales.
        """
        return validate_no_special_chars(v)
    
    @field_validator('nombre')
    def validate_no_xss_nombre(cls: Type['PlotCreate'], v: str) -> str:
        """Valida que el nombre no contenga XSS.

        Args:
            cls: Clase del validador.
            v (str): Valor del nombre a validar.

        Returns:
            str: El valor validado.

        Raises:
            ValueError: Si el nombre contiene XSS.
        """
        return validate_no_xss(v)

class PlotResponse(BaseModel):
    """Schema para la respuesta con información de un lote.

    Este modelo define la estructura de la respuesta que incluye los detalles de un lote.

    Attributes:
        id (int): Identificador único del lote.
        nombre (str): Nombre del lote.
        area (Decimal): Área del lote.
        unidad_area (str): Unidad de medida del área.
        latitud (Decimal): Latitud del lote.
        longitud (Decimal): Longitud del lote.
        finca_id (int): ID de la finca a la que pertenece el lote.
        costos_mantenimiento (Decimal): Costos de mantenimiento del lote.
        moneda (str): Nombre de la moneda del lote.
    """
    id: int
    nombre: str
    area: Decimal
    unidad_area: str
    latitud: Decimal
    longitud: Decimal
    finca_id: int
    costos_mantenimiento: Decimal
    moneda: str

    model_config = ConfigDict(from_attributes=True)
    
class PaginatedPlotListResponse(BaseModel):
    """Schema para la respuesta paginada de lista de lotes.

    Este modelo define la estructura de la respuesta que incluye una lista de lotes
    y la información de paginación.

    Attributes:
        plots (List[PlotResponse]): Lista de lotes para la página actual.
        total_plots (int): Número total de lotes.
        page (int): Número de página actual.
        per_page (int): Cantidad de elementos por página.
        total_pages (int): Número total de páginas.
    """
    plots: List[PlotResponse]
    total_plots: int
    page: int
    per_page: int
    total_pages: int