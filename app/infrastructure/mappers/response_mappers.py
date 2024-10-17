from app.cultural_practices.domain.schemas import TaskResponse
from app.user.domain.schemas import UserResponse
from app.farm.domain.schemas import FarmResponse
from app.plot.domain.schemas import PlotResponse

def map_user_to_response(user) -> UserResponse:
    farm_roles = [
        {
            "rol": ufr.rol.nombre,
            "finca": ufr.finca.nombre if ufr.finca else None
        }
        for ufr in user.roles_fincas
    ]
    
    if not farm_roles:
        farm_roles = [{"rol": "Rol no asignado", "finca": "Ninguna finca asociada"}]
    
    return UserResponse(
        id=user.id,
        nombre=user.nombre,
        apellido=user.apellido,
        email=user.email,
        estado=user.estado.nombre if user.estado else "Desconocido",
        roles_fincas=farm_roles
    )

def map_farm_to_response(farm) -> FarmResponse:
    return FarmResponse(
        id=farm.id,
        nombre=farm.nombre,
        ubicacion=farm.ubicacion,
        area_total=farm.area_total,
        unidad_area=farm.unidad_area.abreviatura if farm.unidad_area else "Desconocida",
        usuarios=[
            map_user_to_response(ufr.usuario)  # Usar map_user_to_response para cada usuario
            for ufr in farm.usuario_roles
        ]
    )

def map_plot_to_response(plot) -> PlotResponse:
    return PlotResponse(
        id=plot.id,
        nombre=plot.nombre,
        area=plot.area,
        unidad_area=plot.unidad_area.abreviatura if plot.unidad_area else "Desconocida",
        latitud=plot.latitud,
        longitud=plot.longitud,
        finca_id=plot.finca_id
    )
    
def map_task_to_response(task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        nombre=task.nombre,
        tipo_labor_id=task.tipo_labor_id,
        fecha_inicio_estimada=task.fecha_inicio_estimada,
        fecha_finalizacion=task.fecha_finalizacion,
        descripcion=task.descripcion,
        estado_id=task.estado_id,
        lote_id=task.lote_id
    )
