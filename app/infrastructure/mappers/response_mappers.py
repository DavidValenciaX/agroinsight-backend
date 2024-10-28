from app.cultural_practices.domain.schemas import TaskResponse, TaskStateResponse, TaskTypeResponse
from app.user.domain.schemas import UserForFarmResponse, UserResponse
from app.farm.domain.schemas import FarmResponse
from app.plot.domain.schemas import PlotResponse
from app.cultural_practices.domain.schemas import TaskTypeResponse
from app.user.infrastructure.orm_models import User

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
    
def map_user_for_farm_to_response(user: User, role_name: str) -> UserForFarmResponse:
    """
    Mapea un usuario a UserForFarmResponse con su rol específico en una finca.

    Args:
        user (User): Usuario a mapear
        farm_id (int): ID de la finca
        role_name (str): Nombre del rol del usuario en la finca específica

    Returns:
        UserForFarmResponse: Respuesta formateada con la información del usuario y su rol en la finca
    """
    return UserForFarmResponse(
        id=user.id,
        nombre=user.nombre,
        apellido=user.apellido,
        email=user.email,
        estado=user.estado.nombre,
        rol=role_name
    )

def map_farm_to_response(farm) -> FarmResponse:
    usuarios = [
        map_user_for_farm_to_response(ufr.usuario, ufr.rol.nombre)
        for ufr in farm.usuario_roles
    ]
    
    return FarmResponse(
        id=farm.id,
        nombre=farm.nombre,
        ubicacion=farm.ubicacion,
        area_total=farm.area_total,
        unidad_area=farm.unidad_area.abreviatura if farm.unidad_area else "Desconocida",
        usuarios=usuarios
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
    
def map_task_state_to_response(task_state) -> TaskStateResponse:
    return TaskStateResponse(
        id=task_state.id,
        nombre=task_state.nombre,
        descripcion=task_state.descripcion
    )

def map_task_type_to_response(task_type: TaskTypeResponse) -> TaskTypeResponse:
    return TaskTypeResponse(
        id=task_type.id,
        nombre=task_type.nombre,
        descripcion=task_type.descripcion
    )
