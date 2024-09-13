from sqlalchemy import Column, Integer, String
from app.infrastructure.db.connection import Base

class EstadoUsuario(Base):
    __tablename__ = "estado_usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, index=True)
    descripcion = Column(String(255))