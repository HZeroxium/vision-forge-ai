# Entry point for the FastAPI application

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import (
    text,
    image,
    video,
    audio,
)  # Import routers (định nghĩa ở bước khác nếu cần)
from app.utils.logger import setup_logger
from app.middlewares.request_logger import RequestLoggerMiddleware
from app.core.config import settings
import os


# Setup logging configuration
setup_logger()

app = FastAPI(title="FastAPI AI Server")

# Add middleware to log incoming requests and responses
app.add_middleware(RequestLoggerMiddleware)

# Create output directory if it doesn't exist
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

# Mount static files directory to serve generated images
app.mount("/images", StaticFiles(directory=settings.OUTPUT_DIR), name="images")

# Include routers (giả định các routers đã được định nghĩa, ở đây chỉ để hoàn thiện kiến trúc)
app.include_router(text.router, prefix="/text")
app.include_router(image.router, prefix="/image")
app.include_router(video.router, prefix="/video")
app.include_router(audio.router, prefix="/audio")

# Run the app using uvicorn when executed directly
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
