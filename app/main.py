# main.py
from fastapi import FastAPI
from app.user.infrastructure.user_api_controller import router
from app.infrastructure.db.connection import engine, Base
from app.user.infrastructure import User, Role, UserRole, EstadoUsuario # Importa todos los modelos

app = FastAPI()

# Crea todas las tablas
Base.metadata.create_all(bind=engine)

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Bienvenido a AgroinSight"}