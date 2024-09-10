from sqlalchemy import Column, Integer, ForeignKey, DateTime
from app.infrastructure.db.connection import Base

class UserRole(Base):
    __tablename__ = "usuario_rol"
    
    usuario_id = Column(Integer, ForeignKey('usuario.id'), primary_key=True)
    rol_id = Column(Integer, ForeignKey('rol.id'), primary_key=True)