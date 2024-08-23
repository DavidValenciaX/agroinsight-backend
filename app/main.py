from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Primera versión del Backend de AgroinSight"}