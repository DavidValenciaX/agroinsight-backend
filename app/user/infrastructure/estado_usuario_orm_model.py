# app/user/infrastructure/estado_usuario_orm_model.py
from sqlalchemy import Column, Integer, String, DateTime
from app.infrastructure.db.connection import Base

class EstadoUsuario(Base):
    __tablename__ = "estado_usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, index=True)
    descripcion = Column(String(255))
    fecha_creacion = Column(DateTime)
    fecha_modificacion = Column(DateTime)