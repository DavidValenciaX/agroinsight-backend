from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base

class Role(Base):
    __tablename__ = "rol"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, index=True)
    descripcion = Column(Text)

    users = relationship("User", secondary="usuario_rol", back_populates="roles")