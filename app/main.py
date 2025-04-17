# app/main.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from app.routers import text, image, video, audio, test
from app.utils.logger import setup_logger
from app.middlewares.request_logger import RequestLoggerMiddleware
from app.middlewares.error_handlers import (
    global_exception_handler,
    http_exception_handler,
)
from app.core.config import settings

setup_logger()

app = FastAPI(title="FastAPI AI Server")

# Add middlewares
app.add_middleware(RequestLoggerMiddleware)

# Register global exception handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Create output directory if it doesn't exist
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

# Mount static files directory to serve generated images
app.mount("/images", StaticFiles(directory=settings.OUTPUT_DIR), name="images")

# Include routers
app.include_router(text.router, prefix="/text")
app.include_router(image.router, prefix="/image")
app.include_router(video.router, prefix="/video")
app.include_router(audio.router, prefix="/audio")
app.include_router(test.router, prefix="/test")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
