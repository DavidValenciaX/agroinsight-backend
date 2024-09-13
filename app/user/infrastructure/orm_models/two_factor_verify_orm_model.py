from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.infrastructure.db.connection import Base

class VerificacionDospasos(Base):
    __tablename__ = "verificacion_dos_pasos"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuario.id', ondelete="CASCADE"), nullable=False)
    pin = Column(String(64), nullable=False, unique=True, index=True)  # Cambiado a 64 caracteres
    expiracion = Column(DateTime, nullable=False)
    intentos = Column(Integer, default=0)

    usuario = relationship("User", back_populates="verificacion_dos_pasos")