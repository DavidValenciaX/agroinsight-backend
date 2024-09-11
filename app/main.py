from fastapi import FastAPI
from app.user.infrastructure.user_api_controller import router
from dotenv import load_dotenv

app = FastAPI()

app.include_router(router)

load_dotenv()

@app.get("/")
async def root():
    return {"message": "Bienvenido a AgroinSight"}