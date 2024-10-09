from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, func
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base
from datetime import datetime, timezone

# Definir constantes para evitar la duplicación de literales
USUARIO_ID = 'usuario.id'
CASCADE_DELETE_ORPHAN = "all, delete-orphan"

class User(Base):
    """
    Representa la tabla 'usuario' en la base de datos.

    Atributos:
    ----------
    - **id** (int): Identificador único del usuario.
    - **nombre** (str): Nombre del usuario.
    - **apellido** (str): Apellido del usuario.
    - **email** (str): Correo electrónico único del usuario.
    - **password** (str): Contraseña del usuario.
    - **failed_attempts** (int): Número de intentos fallidos de inicio de sesión.
    - **locked_until** (datetime): Fecha y hora hasta la cual el usuario está bloqueado.
    - **state_id** (int): Identificador del estado del usuario.
    - **estado** (EstadoUsuario): Estado actual del usuario.
    - **confirmacion** (ConfirmacionUsuario): Información de confirmación del usuario.
    - **verificacion_dos_pasos** (VerificacionDospasos): Información de verificación de dos pasos.
    - **recuperacion_contrasena** (RecuperacionContrasena): Información de recuperación de contraseña.
    - **blacklisted_tokens** (List[BlacklistedToken]): Lista de tokens en lista negra.
    - **fincas** (List[Finca]): Lista de fincas asociadas al usuario.
    - **asignaciones** (List[Asignacion]): Lista de asignaciones del usuario.
    """
    __tablename__ = "usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), index=True)
    apellido = Column(String(50), index=True)
    email = Column(String(100), unique=True, index=True)
    password = Column(String(255))
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    state_id = Column(Integer, ForeignKey('estado_usuario.id'), nullable=False)

    estado = relationship("EstadoUsuario")
    confirmacion = relationship("ConfirmacionUsuario", back_populates="usuario", uselist=False, cascade=CASCADE_DELETE_ORPHAN)
    verificacion_dos_pasos = relationship("VerificacionDospasos", back_populates="usuario", uselist=False, cascade=CASCADE_DELETE_ORPHAN)
    recuperacion_contrasena = relationship("RecuperacionContrasena", back_populates="usuario", uselist=False, cascade=CASCADE_DELETE_ORPHAN)
    blacklisted_tokens = relationship("BlacklistedToken", back_populates="usuario")
    asignaciones = relationship("Asignacion", back_populates="usuario")
    roles_fincas = relationship("UsuarioFincaRol", back_populates="usuario")

class UsuarioFincaRol(Base):
    __tablename__ = "usuario_finca_rol"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('usuario.id'), nullable=False)
    finca_id = Column(Integer, ForeignKey('finca.id'), nullable=True)
    rol_id = Column(Integer, ForeignKey('rol.id'), nullable=False)

    usuario = relationship("User", back_populates="roles_fincas")
    finca = relationship("Finca", back_populates="usuario_roles")
    rol = relationship("Role", back_populates="usuario_fincas")
    
class Role(Base):
    """
    Representa la tabla 'rol' en la base de datos.

    Atributos:
    ----------
    - **id** (int): Identificador único del rol.
    - **nombre** (str): Nombre único del rol.
    - **descripcion** (str): Descripción del rol.
    - **users** (List[User]): Lista de usuarios asociados al rol.
    """
    __tablename__ = "rol"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, index=True)
    descripcion = Column(Text)

    usuario_fincas = relationship("UsuarioFincaRol", back_populates="rol")
    
class EstadoUsuario(Base):
    """
    Representa la tabla 'estado_usuario' en la base de datos.

    Atributos:
    ----------
    - **id** (int): Identificador único del estado.
    - **nombre** (str): Nombre único del estado.
    - **descripcion** (str): Descripción del estado.
    """
    __tablename__ = "estado_usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, index=True)
    descripcion = Column(String(255))
    
class ConfirmacionUsuario(Base):
    """
    Representa la tabla 'confirmacion_usuario' en la base de datos.

    Atributos:
    ----------
    - **id** (int): Identificador único de la confirmación.
    - **usuario_id** (int): Identificador del usuario asociado.
    - **pin** (str): PIN único de confirmación.
    - **expiracion** (datetime): Fecha y hora de expiración del PIN.
    - **intentos** (int): Número de intentos de confirmación.
    - **usuario** (User): Usuario asociado a la confirmación.
    """
    __tablename__ = "confirmacion_usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey(USUARIO_ID, ondelete="CASCADE"), nullable=False)
    pin = Column(String(64), nullable=False, unique=True, index=True)
    expiracion = Column(DateTime, nullable=False)
    intentos = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.utc_timestamp())
    resends = Column(Integer, default=0)

    usuario = relationship("User", back_populates="confirmacion")
    
class VerificacionDospasos(Base):
    """
    Representa la tabla 'verificacion_dos_pasos' en la base de datos.

    Atributos:
    ----------
    - **id** (int): Identificador único de la verificación.
    - **usuario_id** (int): Identificador del usuario asociado.
    - **pin** (str): PIN único de verificación.
    - **expiracion** (datetime): Fecha y hora de expiración del PIN.
    - **intentos** (int): Número de intentos de verificación.
    - **usuario** (User): Usuario asociado a la verificación.
    """
    __tablename__ = "verificacion_dos_pasos"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey(USUARIO_ID, ondelete="CASCADE"), nullable=False)
    pin = Column(String(64), nullable=False, unique=True, index=True)
    expiracion = Column(DateTime, nullable=False)
    intentos = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.utc_timestamp())
    resends = Column(Integer, default=0)

    usuario = relationship("User", back_populates="verificacion_dos_pasos")
    
class RecuperacionContrasena(Base):
    """
    Representa la tabla 'recuperacion_contrasena' en la base de datos.

    Atributos:
    ----------
    - **id** (int): Identificador único de la recuperación.
    - **usuario_id** (int): Identificador del usuario asociado.
    - **pin** (str): PIN único de recuperación.
    - **expiracion** (datetime): Fecha y hora de expiración del PIN.
    - **intentos** (int): Número de intentos de recuperación.
    - **pin_confirmado** (bool): Indica si el PIN ha sido confirmado.
    - **usuario** (User): Usuario asociado a la recuperación.
    """
    __tablename__ = "recuperacion_contrasena"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey(USUARIO_ID, ondelete="CASCADE"), nullable=False)
    pin = Column(String(64), nullable=False, unique=True, index=True)
    expiracion = Column(DateTime, nullable=False)
    intentos = Column(Integer, default=0)
    pin_confirmado = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.utc_timestamp())
    resends = Column(Integer, default=0)

    usuario = relationship("User", back_populates="recuperacion_contrasena")
    
class BlacklistedToken(Base):
    """
    Representa la tabla 'blacklisted_tokens' en la base de datos.

    Atributos:
    ----------
    - **id** (int): Identificador único del token en lista negra.
    - **token** (str): Token único en lista negra.
    - **blacklisted_at** (datetime): Fecha y hora en que el token fue añadido a la lista negra.
    - **usuario_id** (int): Identificador del usuario asociado.
    - **usuario** (User): Usuario asociado al token en lista negra.
    """
    __tablename__ = "blacklisted_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    blacklisted_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    usuario_id = Column(Integer, ForeignKey(USUARIO_ID), nullable=False)
    usuario = relationship("User", back_populates="blacklisted_tokens")