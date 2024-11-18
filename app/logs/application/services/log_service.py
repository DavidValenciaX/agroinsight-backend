from enum import Enum
from typing import Optional, Dict, Any, Union
from fastapi import Request
from app.logs.domain.schemas import ActivityLogCreate, LogSeverity
from app.logs.infrastructure.sql_repository import LogRepository
from app.user.domain.schemas import UserInDB
from app.user.infrastructure.sql_repository import UserRepository

class LogActionType(str, Enum):
    """Enumeración para los tipos de acciones comunes en los logs."""
    CREATE = "CREAR"
    UPDATE = "ACTUALIZAR"
    DELETE = "ELIMINAR"
    LOGIN = "INICIAR_SESION"
    LOGOUT = "CERRAR_SESION"
    VIEW = "VISUALIZAR"
    EXPORT = "EXPORTAR"
    IMPORT = "IMPORTAR"
    GENERATE_REPORT = "GENERAR_REPORTE"
    REGISTER_COSTS = "REGISTRAR_COSTOS"
    REGISTER_HARVEST = "REGISTRAR_COSECHA"
    REGISTER_SOIL_ANALYSIS = "REGISTRAR_ANALISIS_SUELO"
    REGISTER_WEATHER = "REGISTRAR_CLIMA"
    ASSIGN_ROLE = "ASIGNAR_ROL"
    CHANGE_STATUS = "CAMBIAR_ESTADO"
    REGISTER_USER = "REGISTRAR_USUARIO"
    UPDATE_PROFILE = "ACTUALIZAR_PERFIL"
    CHANGE_PASSWORD = "CAMBIAR_CONTRASEÑA"
    REGISTER_TASK = "REGISTRAR_TAREA"
    ASSIGN_TASK = "ASIGNAR_TAREA"
    COMPLETE_TASK = "COMPLETAR_TAREA"
    REGISTER_PEST = "REGISTRAR_PLAGA"
    REGISTER_MONITORING = "REGISTRAR_MONITOREO"
    REGISTER_FARM = "REGISTRAR_FINCA"
    REGISTER_PLOT = "REGISTRAR_LOTE"
    ASSIGN_USER_TO_FARM = "ASIGNAR_USUARIO_FINCA"
    CONFIRM_REGISTRATION = "CONFIRM_REGISTRATION"
    VERIFY_2FA = "VERIFY_2FA"
    PASSWORD_RECOVERY = "PASSWORD_RECOVERY"
    CONFIRM_RECOVERY = "CONFIRM_RECOVERY"
    RESEND_PIN = "RESEND_PIN"

class LogService:
    """Servicio para gestionar la lógica de negocio relacionada con logs."""

    def __init__(self, repository: LogRepository):
        """Inicializa el servicio con un repositorio."""
        self.repository = repository
        self.user_repository = UserRepository(repository.db)

    def _ensure_action_type_exists(self, action_type: LogActionType) -> int:
        """Asegura que existe el tipo de acción y devuelve su ID."""
        existing_type = self.repository.get_action_type_by_name(action_type.value)
        if not existing_type:
            new_type = self.repository.create_action_type({
                "nombre": action_type.value,
                "descripcion": f"Acción de {action_type.value.lower()}"
            })
            return new_type.id
        return existing_type.id

    def log_activity(
        self,
        user: Optional[Union[UserInDB, str]] = None,
        action_type: str = None,
        table_name: str = None,
        request: Request = None,
        record_id: Optional[int] = None,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        severity: LogSeverity = LogSeverity.INFO,
        description: Optional[str] = None
    ) -> None:
        """
        Registra una actividad en el log.
        
        Args:
            user: Usuario o email del usuario que realiza la acción
            action_type: Tipo de acción realizada
            table_name: Nombre de la tabla afectada
            request: Objeto Request de FastAPI
            record_id: ID del registro afectado
            old_value: Valor anterior del registro
            new_value: Nuevo valor del registro
            severity: Nivel de severidad del log
            description: Descripción adicional del log
        """
        # Determinar el ID del usuario
        usuario_id = None
        if isinstance(user, UserInDB):
            usuario_id = user.id
            user_description = f"Usuario ID: {user.id}"
        elif isinstance(user, str):  # Es un email
            usuario = self.user_repository.get_user_by_email(user)
            if usuario:
                usuario_id = usuario.id
                user_description = f"Usuario ID: {usuario.id}"
            else:
                user_description = f"Usuario no registrado (Email: {user})"
        else:
            user_description = "Usuario no identificado"

        # Crear la descripción completa
        full_description = f"{user_description}. {description or ''}"

        log_data = ActivityLogCreate(
            usuario_id=usuario_id,  # Puede ser None
            tipo_accion_id=self._ensure_action_type_exists(action_type),
            tabla_afectada=table_name,
            registro_id=record_id,
            valor_anterior=old_value,
            valor_nuevo=new_value,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            severidad=severity,
            descripcion=full_description
        )
        
        self.repository.create_activity_log(log_data) 