#app/user/domain/user_entities.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    nombre: str
    apellido: str
    email: str
    password: str
    state_id: int = 1

class UserInDB(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str
    password: str
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None
    state_id: int

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
