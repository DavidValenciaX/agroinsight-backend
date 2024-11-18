from sqlalchemy import TIMESTAMP, Column, Integer, String, ForeignKey, Text, Boolean, func
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base

# Definir constantes para evitar la duplicación de literales
USUARIO_ID = 'usuario.id'
CASCADE_DELETE_ORPHAN = "all, delete-orphan"

class User(Base):
    """
    Representa la tabla 'usuario' en la base de datos.

    Attributes:
        id (int): Identificador único del usuario.
        nombre (str): Nombre del usuario.
        apellido (str): Apellido del usuario.
        email (str): Correo electrónico único del usuario.
        password (str): Contraseña del usuario.
        failed_attempts (int): Número de intentos fallidos de inicio de sesión.
        locked_until (datetime): Fecha y hora hasta la cual el usuario está bloqueado.
        state_id (int): Identificador del estado del usuario.
        estado (UserState): Estado actual del usuario.
        confirmacion (UserConfirmation): Información de confirmación del usuario.
        verificacion_dos_pasos (TwoStepVerification): Información de verificación de dos pasos.
        recuperacion_contrasena (PasswordRecovery): Información de recuperación de contraseña.
        blacklisted_tokens (List[BlacklistedToken]): Lista de tokens en lista negra.
        asignaciones (List[Assignment]): Lista de asignaciones del usuario.
        roles_fincas (List[UserFarmRole]): Lista de roles del usuario en diferentes fincas.
        logs (List[ActivityLog]): Lista de registros de actividad del usuario.
    """
    __tablename__ = "usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False, index=True)
    apellido = Column(String(50), nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    failed_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(TIMESTAMP(timezone=True), nullable=True)  # Actualizado a TIMESTAMP
    state_id = Column(Integer, ForeignKey('estado_usuario.id'), nullable=False)
    acepta_terminos = Column(Boolean, nullable=False, default=False)

    estado = relationship("UserState")
    confirmacion = relationship("UserConfirmation", back_populates="usuario", cascade=CASCADE_DELETE_ORPHAN)
    verificacion_dos_pasos = relationship("TwoStepVerification", back_populates="usuario", cascade=CASCADE_DELETE_ORPHAN)
    recuperacion_contrasena = relationship("PasswordRecovery", back_populates="usuario", cascade=CASCADE_DELETE_ORPHAN)
    blacklisted_tokens = relationship("BlacklistedToken", back_populates="usuario", cascade=CASCADE_DELETE_ORPHAN)
    asignaciones = relationship("Assignment", back_populates="usuario", cascade=CASCADE_DELETE_ORPHAN)
    roles_fincas = relationship("UserFarmRole", back_populates="usuario", cascade=CASCADE_DELETE_ORPHAN)
    logs = relationship("ActivityLog", back_populates="usuario", cascade="all, delete-orphan")

class UserFarmRole(Base):
    """
    Representa la tabla 'usuario_finca_rol' en la base de datos.

    Attributes:
        id (int): Identificador único de la relación usuario-finca-rol.
        usuario_id (int): Identificador del usuario.
        finca_id (int): Identificador de la finca.
        rol_id (int): Identificador del rol.
        usuario (User): Usuario asociado.
        finca (Farm): Finca asociada.
        rol (Role): Rol asociado.
    """
    __tablename__ = "usuario_finca_rol"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('usuario.id'), nullable=False)
    finca_id = Column(Integer, ForeignKey('finca.id'), nullable=False)
    rol_id = Column(Integer, ForeignKey('rol.id'), nullable=False)

    usuario = relationship("User", back_populates="roles_fincas")
    finca = relationship("Farm", back_populates="usuario_roles")
    rol = relationship("Role", back_populates="usuario_fincas")
    
class Role(Base):
    """
    Representa la tabla 'rol' en la base de datos.

    Attributes:
        id (int): Identificador único del rol.
        nombre (str): Nombre único del rol.
        descripcion (str): Descripción del rol.
        usuario_fincas (List[UserFarmRole]): Lista de relaciones usuario-finca-rol asociadas a este rol.
    """
    __tablename__ = "rol"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False, index=True)
    descripcion = Column(Text)

    usuario_fincas = relationship("UserFarmRole", back_populates="rol")
    
class UserState(Base):
    """
    Representa la tabla 'estado_usuario' en la base de datos.

    Attributes:
        id (int): Identificador único del estado.
        nombre (str): Nombre único del estado.
        descripcion (str): Descripción del estado.
    """
    __tablename__ = "estado_usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False, index=True)
    descripcion = Column(Text)
    
class UserConfirmation(Base):
    """
    Representa la tabla 'confirmacion_usuario' en la base de datos.

    Attributes:
        id (int): Identificador único de la confirmación.
        usuario_id (int): Identificador del usuario asociado.
        pin (str): PIN único de confirmación.
        expiracion (datetime): Fecha y hora de expiración del PIN.
        intentos (int): Número de intentos de confirmación.
        created_at (datetime): Fecha y hora de creación del registro.
        resends (int): Número de reenvíos del PIN.
        usuario (User): Usuario asociado a la confirmación.
    """
    __tablename__ = "confirmacion_usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey(USUARIO_ID, ondelete="CASCADE"), nullable=False)
    pin = Column(String(64), nullable=False, unique=True, index=True)
    expiracion = Column(TIMESTAMP(timezone=True), nullable=False)
    intentos = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.timezone('UTC', func.current_timestamp()))
    resends = Column(Integer, default=0)

    usuario = relationship("User", back_populates="confirmacion")
    
class TwoStepVerification(Base):
    """
    Representa la tabla 'verificacion_dos_pasos' en la base de datos.

    Attributes:
        id (int): Identificador único de la verificación.
        usuario_id (int): Identificador del usuario asociado.
        pin (str): PIN único de verificación.
        expiracion (datetime): Fecha y hora de expiración del PIN.
        intentos (int): Número de intentos de verificación.
        created_at (datetime): Fecha y hora de creación del registro.
        resends (int): Número de reenvíos del PIN.
        usuario (User): Usuario asociado a la verificación.
    """
    __tablename__ = "verificacion_dos_pasos"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey(USUARIO_ID, ondelete="CASCADE"), nullable=False)
    pin = Column(String(64), nullable=False, unique=True, index=True)
    expiracion = Column(TIMESTAMP(timezone=True), nullable=False)
    intentos = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.timezone('UTC', func.current_timestamp()))
    resends = Column(Integer, default=0)

    usuario = relationship("User", back_populates="verificacion_dos_pasos")
    
class PasswordRecovery(Base):
    """
    Representa la tabla 'recuperacion_contrasena' en la base de datos.

    Attributes:
        id (int): Identificador único de la recuperación.
        usuario_id (int): Identificador del usuario asociado.
        pin (str): PIN único de recuperación.
        expiracion (datetime): Fecha y hora de expiración del PIN.
        intentos (int): Número de intentos de recuperación.
        pin_confirmado (bool): Indica si el PIN ha sido confirmado.
        created_at (datetime): Fecha y hora de creación del registro.
        resends (int): Número de reenvíos del PIN.
        usuario (User): Usuario asociado a la recuperación.
    """
    __tablename__ = "recuperacion_contrasena"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey(USUARIO_ID, ondelete="CASCADE"), nullable=False)
    pin = Column(String(64), nullable=False, unique=True, index=True)
    expiracion = Column(TIMESTAMP(timezone=True), nullable=False)
    intentos = Column(Integer, default=0)
    pin_confirmado = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.timezone('UTC', func.current_timestamp()))
    resends = Column(Integer, default=0)

    usuario = relationship("User", back_populates="recuperacion_contrasena")
    
class BlacklistedToken(Base):
    """
    Representa la tabla 'blacklisted_tokens' en la base de datos.

    Attributes:
        id (int): Identificador único del token en lista negra.
        token (str): Token único en lista negra.
        blacklisted_at (datetime): Fecha y hora en que el token fue añadido a la lista negra.
        usuario_id (int): Identificador del usuario asociado.
        usuario (User): Usuario asociado al token en lista negra.
    """
    __tablename__ = "blacklisted_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    blacklisted_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.timezone('UTC', func.current_timestamp()))
    usuario_id = Column(Integer, ForeignKey(USUARIO_ID), nullable=False)
    
    usuario = relationship("User", back_populates="blacklisted_tokens")
