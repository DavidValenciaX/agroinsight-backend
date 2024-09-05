#app/user/infrastructure/user_orm_model
from sqlalchemy import Column, Integer, String, DateTime, event
from sqlalchemy.orm import declarative_base
from app.core.security.security_utils import hash_password

Base = declarative_base()

class User(Base):
    __tablename__ = "usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), index=True)
    apellido = Column(String(50), index=True)
    email = Column(String(100), unique=True, index=True)
    password = Column(String(255))
    failed_attempts = Column(Integer, default=0)  # Número de intentos fallidos
    locked_until = Column(DateTime, nullable=True)  # Tiempo hasta el que la cuenta está bloqueada
    state_id = Column (Integer)