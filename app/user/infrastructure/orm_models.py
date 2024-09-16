from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base

class User(Base):
    __tablename__ = "usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), index=True)
    apellido = Column(String(50), index=True)
    email = Column(String(100), unique=True, index=True)
    password = Column(String(255))
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    state_id = Column(Integer, ForeignKey('estado_usuario.id'), nullable=False)

    roles = relationship("Role", secondary="usuario_rol", back_populates="users")
    estado = relationship("EstadoUsuario") 
    confirmacion = relationship("ConfirmacionUsuario", back_populates="usuario", uselist=False, cascade="all, delete-orphan")
    verificacion_dos_pasos = relationship("VerificacionDospasos", back_populates="usuario", uselist=False, cascade="all, delete-orphan")
    recuperacion_contrasena = relationship("RecuperacionContrasena", back_populates="usuario", uselist=False, cascade="all, delete-orphan")
    
class UserRole(Base):
    __tablename__ = "usuario_rol"
    
    usuario_id = Column(Integer, ForeignKey('usuario.id'), primary_key=True)
    rol_id = Column(Integer, ForeignKey('rol.id'), primary_key=True)
    
class Role(Base):
    __tablename__ = "rol"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, index=True)
    descripcion = Column(Text)

    users = relationship("User", secondary="usuario_rol", back_populates="roles")
    
class EstadoUsuario(Base):
    __tablename__ = "estado_usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, index=True)
    descripcion = Column(String(255))
    
class ConfirmacionUsuario(Base):
    __tablename__ = "confirmacion_usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuario.id', ondelete="CASCADE"), nullable=False)
    pin = Column(String(64), nullable=False, unique=True, index=True)
    expiracion = Column(DateTime, nullable=False)
    intentos = Column(Integer, default=0)

    usuario = relationship("User", back_populates="confirmacion")
    
class VerificacionDospasos(Base):
    __tablename__ = "verificacion_dos_pasos"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuario.id', ondelete="CASCADE"), nullable=False)
    pin = Column(String(64), nullable=False, unique=True, index=True)
    expiracion = Column(DateTime, nullable=False)
    intentos = Column(Integer, default=0)

    usuario = relationship("User", back_populates="verificacion_dos_pasos")
    
class RecuperacionContrasena(Base):
    __tablename__ = "recuperacion_contrasena"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuario.id', ondelete="CASCADE"), nullable=False)
    pin = Column(String(64), nullable=False, unique=True, index=True)
    expiracion = Column(DateTime, nullable=False)
    intentos = Column(Integer, default=0)

    usuario = relationship("User", back_populates="recuperacion_contrasena")