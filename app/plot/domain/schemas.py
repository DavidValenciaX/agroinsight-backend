from pydantic import BaseModel, Field
from decimal import Decimal
from typing import List

class PlotCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    area: Decimal = Field(..., gt=0)
    unidad_area_id: int
    latitud: Decimal = Field(..., ge=-90, le=90)
    longitud: Decimal = Field(..., ge=-180, le=180)
    finca_id: int

class PlotResponse(BaseModel):
    id: int
    nombre: str
    area: Decimal
    unidad_area: str
    latitud: Decimal
    longitud: Decimal
    finca_id: int

    class Config:
        from_attributes = True
    
class PaginatedPlotListResponse(BaseModel):
    plots: List[PlotResponse]
    total_plots: int
    page: int
    per_page: int
    total_pages: int