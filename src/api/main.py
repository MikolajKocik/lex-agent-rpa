from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="RPA autonomous agent microservice",
    description="Manages an archive and legal documentation.",
    version="0.1.0"
)

app.include_router(router, prefix="/api")
