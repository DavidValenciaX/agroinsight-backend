from fastapi import FastAPI
from app.user.infrastructure.user_api_controller import router

app = FastAPI()

app.include_router(router)
