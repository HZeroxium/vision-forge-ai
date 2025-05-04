# app/main.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from app.routers import text, image, video, audio, storage
from app.routers.pinecone import (
    text as pinecone_text,
    image as pinecone_image,
    audio as pinecone_audio,
)
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
app.include_router(text.router, prefix="/api", tags=["text"])
app.include_router(image.router, prefix="/image", tags=["image"])
app.include_router(video.router, prefix="/video", tags=["video"])
app.include_router(audio.router, prefix="/audio", tags=["audio"])
app.include_router(storage.router, prefix="/storage", tags=["storage"])

# Include pinecone routers
app.include_router(pinecone_text.router, prefix="/api/pinecone", tags=["pinecone"])
app.include_router(pinecone_image.router, prefix="/api/pinecone", tags=["pinecone"])
app.include_router(pinecone_audio.router, prefix="/api/pinecone", tags=["pinecone"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
