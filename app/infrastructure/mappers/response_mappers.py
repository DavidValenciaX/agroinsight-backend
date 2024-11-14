from app.costs.domain.schemas import AgriculturalInputCategoryResponse, AgriculturalInputResponse
from app.cultural_practices.domain.schemas import TaskResponse, TaskStateResponse, TaskTypeResponse
from app.costs.infrastructure.orm_models import AgriculturalInput, AgriculturalInputCategory
from app.cultural_practices.infrastructure.orm_models import CulturalTask
from app.user.domain.schemas import UserForFarmResponse, UserResponse
from app.farm.domain.schemas import FarmResponse, WorkerFarmResponse
from app.plot.domain.schemas import PlotResponse
from app.cultural_practices.domain.schemas import TaskTypeResponse
from app.user.infrastructure.orm_models import User

def map_user_to_response(user) -> UserResponse:
    """
    Mapea un objeto de usuario a un esquema de respuesta de usuario.

    Args:
        user (User): Objeto de usuario a mapear.

    Returns:
        UserResponse: Esquema de respuesta con la información del usuario.
    """
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
        user (User): Usuario a mapear.
        role_name (str): Nombre del rol del usuario en la finca específica.

    Returns:
        UserForFarmResponse: Respuesta formateada con la información del usuario y su rol en la finca.
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
    """
    Mapea un objeto de finca a un esquema de respuesta de finca.

    Args:
        farm: Objeto de finca a mapear.

    Returns:
        FarmResponse: Esquema de respuesta con la información de la finca.
    """
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
    
def map_worker_farm_to_response(farm) -> FarmResponse:
    """
    Mapea un objeto de finca a un esquema de respuesta de finca.

    Args:
        farm: Objeto de finca a mapear.

    Returns:
        WorkerFarmResponse: Esquema de respuesta con la información de la finca.
    """
    
    return WorkerFarmResponse(
        id=farm.id,
        nombre=farm.nombre,
        ubicacion=farm.ubicacion
    )

def map_plot_to_response(plot) -> PlotResponse:
    """
    Mapea un objeto de parcela a un esquema de respuesta de parcela.

    Args:
        plot: Objeto de parcela a mapear.

    Returns:
        PlotResponse: Esquema de respuesta con la información de la parcela.
    """
    return PlotResponse(
        id=plot.id,
        nombre=plot.nombre,
        area=plot.area,
        unidad_area=plot.unidad_area.abreviatura if plot.unidad_area else "Desconocida",
        latitud=plot.latitud,
        longitud=plot.longitud,
        finca_id=plot.finca_id
    )
    
def map_task_to_response(task: CulturalTask) -> TaskResponse:
    """Mapea una tarea a su modelo de respuesta.

    Args:
        task (CulturalTask): Tarea a mapear.

    Returns:
        TaskResponse: Modelo de respuesta de la tarea.
    """
    return TaskResponse(
        id=task.id,
        nombre=task.nombre,
        tipo_labor_id=task.tipo_labor_id,
        tipo_labor_nombre=task.tipo_labor.nombre,
        fecha_inicio_estimada=task.fecha_inicio_estimada,
        fecha_finalizacion=task.fecha_finalizacion,
        descripcion=task.descripcion,
        estado_id=task.estado_id,
        estado_nombre=task.estado.nombre,
        lote_id=task.lote_id
    )
    
def map_task_state_to_response(task_state) -> TaskStateResponse:
    """
    Mapea un objeto de estado de tarea a un esquema de respuesta de estado de tarea.

    Args:
        task_state: Objeto de estado de tarea a mapear.

    Returns:
        TaskStateResponse: Esquema de respuesta con la información del estado de la tarea.
    """
    return TaskStateResponse(
        id=task_state.id,
        nombre=task_state.nombre,
        descripcion=task_state.descripcion
    )

def map_task_type_to_response(task_type: TaskTypeResponse) -> TaskTypeResponse:
    """
    Mapea un objeto de tipo de tarea a un esquema de respuesta de tipo de tarea.

    Args:
        task_type (TaskTypeResponse): Objeto de tipo de tarea a mapear.

    Returns:
        TaskTypeResponse: Esquema de respuesta con la información del tipo de tarea.
    """
    return TaskTypeResponse(
        id=task_type.id,
        nombre=task_type.nombre,
        descripcion=task_type.descripcion
    )

def map_input_category_to_response(category: AgriculturalInputCategory) -> AgriculturalInputCategoryResponse:
    """Mapea una categoría de insumo a su modelo de respuesta.

    Args:
        category (AgriculturalInputCategory): Categoría de insumo a mapear.

    Returns:
        AgriculturalInputCategoryResponse: Modelo de respuesta de la categoría.
    """
    return AgriculturalInputCategoryResponse(
        id=category.id,
        nombre=category.nombre,
        descripcion=category.descripcion
    )
    
def map_agricultural_input_to_response(input: AgriculturalInput) -> AgriculturalInputResponse:
    """Mapea un insumo agrícola a su modelo de respuesta.

    Args:
        input (AgriculturalInput): Insumo agrícola a mapear.

    Returns:
        AgriculturalInputResponse: Modelo de respuesta del insumo.
    """
    return AgriculturalInputResponse(
        id=input.id,
        categoria_id=input.categoria_id,
        categoria_nombre=input.categoria.nombre,
        nombre=input.nombre,
        descripcion=input.descripcion,
        unidad_medida_id=input.unidad_medida_id,
        unidad_medida_nombre=input.unidad_medida.nombre,
        costo_unitario=input.costo_unitario,
        stock_actual=input.stock_actual
    )