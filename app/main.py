from fastapi import FastAPI
from app.user.infrastructure.user_api_controller import router
from app.infrastructure.db.connection import engine, Base, SessionLocal
from app.user.infrastructure import User, Role, UserRole, EstadoUsuario
from app.user.infrastructure.confirmacion_usuario_orm_model import ConfirmacionUsuario
from apscheduler.schedulers.background import BackgroundScheduler
""" from app.core.services.email_service import clean_expired_registrations """
from dotenv import load_dotenv

app = FastAPI()

app.include_router(router)

load_dotenv()

@app.get("/")
async def root():
    return {"message": "Bienvenido a AgroinSight"}

# Configurar el scheduler
""" scheduler = BackgroundScheduler()
scheduler.add_job(clean_expired_registrations, 'interval', minutes=10, args=[SessionLocal()])
scheduler.start() """

# Asegúrate de apagar el scheduler cuando la aplicación se cierre
""" @app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown() """