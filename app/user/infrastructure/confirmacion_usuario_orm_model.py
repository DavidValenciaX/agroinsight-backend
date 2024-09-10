from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base

class ConfirmacionUsuario(Base):
    __tablename__ = "confirmacion_usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuario.id', ondelete="CASCADE"), nullable=False)
    pin = Column(String(4), nullable=False)
    expiracion = Column(DateTime, nullable=False)
    intentos = Column(Integer, default=0)

    usuario = relationship("User", back_populates="confirmacion")