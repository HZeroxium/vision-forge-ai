# app/utils/error_handlers.py
# Custom error handlers to catch and format exceptions

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

# Handler for HTTP exceptions
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

# Additional error handlers can be implemented here if needed
