from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
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