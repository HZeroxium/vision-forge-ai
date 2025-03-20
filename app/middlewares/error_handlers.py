# app/middlewares/error_handler.py
import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger("error_handler")


async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to catch and log exceptions."""
    logger.exception(f"Unhandled error occurred: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error. Please contact support."},
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler for HTTP exceptions."""
    logger.error(f"HTTP Exception: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})
