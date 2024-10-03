
from app.cultural_practices.domain.schemas import AssignmentResponse
from app.user.domain.schemas import UserResponse
from app.farm.domain.schemas import FarmResponse
from app.plot.domain.schemas import PlotResponse

def map_user_to_response(user) -> UserResponse:
    return UserResponse(
        id=user.id,
        nombre=user.nombre,
        apellido=user.apellido,
        email=user.email,
        estado=user.estado.nombre if user.estado else "Desconocido",
        rol=", ".join([role.nombre for role in user.roles]) if user.roles else "Rol no asignado",
        fincas=[finca.nombre for finca in user.fincas]
    )

def map_farm_to_response(farm) -> FarmResponse:
    return FarmResponse(
        id=farm.id,
        nombre=farm.nombre,
        ubicacion=farm.ubicacion,
        area_total=farm.area_total,
        unidad_area=farm.unidad_area.abreviatura if farm.unidad_area else "Desconocida",
        latitud=farm.latitud,
        longitud=farm.longitud
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
    
def map_assignment_to_response(assignment) -> AssignmentResponse:
    return AssignmentResponse(
        usuario_id=assignment.usuario_id,
        tarea_labor_cultural_id=assignment.tarea_labor_cultural_id,
        notas=assignment.notas
    )