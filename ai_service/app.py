# ai_service/app.py
from fastapi import FastAPI
from ai_service.routers import image_routes, text_routes


def create_app() -> FastAPI:
    app = FastAPI(title="Vision Forge AI", version="1.0.0")
    app.include_router(image_routes.router, prefix="/api/v1/images", tags=["Images"])
    app.include_router(text_routes.router, prefix="/api/v1/text", tags=["Text"])
    return app
