from pydantic import BaseModel
from typing import Optional, Any
from datetime import date, time

class WeatherAPIResponse(BaseModel):
    """Modelo de respuesta para la prueba de la API de OpenWeatherMap.
    
    Attributes:
        success (bool): Indica si la llamada a la API fue exitosa.
        message (str): Mensaje descriptivo del resultado.
        data (Optional[Any]): Datos recibidos de la API, si los hay.
    """
    success: bool
    message: str
    data: Optional[Any] = None 

class WeatherLogCreate(BaseModel):
    lote_id: int
    fecha: date
    hora: time
    temperatura: float
    temperatura_sensacion: float
    temperatura_unidad_id: Optional[int]
    presion_atmosferica: float
    presion_unidad_id: Optional[int]
    humedad_relativa: float
    humedad_unidad_id: Optional[int]
    precipitacion: Optional[float]
    precipitacion_unidad_id: Optional[int]
    indice_uv: float
    nubosidad: float
    nubosidad_unidad_id: Optional[int]
    velocidad_viento: float
    velocidad_viento_unidad_id: Optional[int]
    direccion_viento: int
    direccion_viento_unidad_id: Optional[int]
    rafaga_viento: Optional[float]
    rafaga_viento_unidad_id: Optional[int]
    visibilidad: Optional[int]
    visibilidad_unidad_id: Optional[int]
    punto_rocio: Optional[float]
    punto_rocio_unidad_id: Optional[int]
    descripcion_clima: Optional[str]
    codigo_clima: Optional[str]

class WeatherLog(WeatherLogCreate):
    id: int

    class Config:
        from_attributes = True 

class WeatherLogResponse(BaseModel):
    id: int
    lote_id: int
    fecha: date
    hora: time
    temperatura: float
    temperatura_sensacion: float
    presion_atmosferica: float
    humedad_relativa: float
    precipitacion: Optional[float]
    indice_uv: float
    nubosidad: float
    velocidad_viento: float
    direccion_viento: int
    rafaga_viento: Optional[float]
    visibilidad: Optional[int]
    punto_rocio: Optional[float]
    descripcion_clima: Optional[str]
    codigo_clima: Optional[str]

    class Config:
        from_attributes = True

class WeatherLogsListResponse(BaseModel):
    success: bool
    message: str
    data: list[WeatherLogResponse] 