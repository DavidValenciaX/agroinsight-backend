from sqlalchemy.orm import Session
from typing import Optional, List
from app.logs.infrastructure.orm_models import ActivityLog, LogActionType
from app.logs.domain.schemas import ActivityLogCreate, LogActionTypeCreate

class LogRepository:
    """Repositorio para gestionar las operaciones de base de datos relacionadas con logs."""

    def __init__(self, db: Session):
        """Inicializa el repositorio con una sesión de base de datos."""
        self.db = db

    def create_activity_log(self, log_data: ActivityLogCreate) -> Optional[ActivityLog]:
        """Crea un nuevo registro de log de actividad."""
        try:
            log = ActivityLog(
                usuario_id=log_data.usuario_id,
                tipo_accion_id=log_data.tipo_accion_id,
                tabla_afectada=log_data.tabla_afectada,
                registro_id=log_data.registro_id,
                valor_anterior=log_data.valor_anterior,
                valor_nuevo=log_data.valor_nuevo,
                ip_address=log_data.ip_address,
                user_agent=log_data.user_agent,
                severidad=log_data.severidad,
                descripcion=log_data.descripcion
            )
            self.db.add(log)
            self.db.commit()
            self.db.refresh(log)
            return log
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear el log de actividad: {e}")
            return None

    def get_action_type_by_name(self, name: str) -> Optional[LogActionType]:
        """Obtiene un tipo de acción por su nombre."""
        return self.db.query(LogActionType).filter(LogActionType.nombre == name).first()

    def create_action_type(self, action_type_data: LogActionTypeCreate) -> Optional[LogActionType]:
        """Crea un nuevo tipo de acción de log."""
        try:
            new_action_type = LogActionType(
                nombre=action_type_data.nombre,
                descripcion=action_type_data.descripcion
            )
            self.db.add(new_action_type)
            self.db.commit()
            self.db.refresh(new_action_type)
            return new_action_type
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear el tipo de acción: {e}")
            return None

    def get_logs_by_user_id(self, user_id: int, limit: int = 100) -> List[ActivityLog]:
        """Obtiene los logs de un usuario específico."""
        return self.db.query(ActivityLog)\
            .filter(ActivityLog.usuario_id == user_id)\
            .order_by(ActivityLog.fecha_creacion.desc())\
            .limit(limit)\
            .all() 

    def get_paginated_logs(self, limit: int = 100, offset: int = 0) -> List[ActivityLog]:
        """Obtiene una lista paginada de logs de actividad."""
        try:
            return self.db.query(ActivityLog)\
                .order_by(ActivityLog.id.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
        except Exception as e:
            print(f"Error al obtener los logs paginados: {e}")
            return []