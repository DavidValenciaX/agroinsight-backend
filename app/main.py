from fastapi import FastAPI
from app.user.infrastructure.controllers.user_api_controller import router

app = FastAPI()

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Bienvenido a AgroinSight"}