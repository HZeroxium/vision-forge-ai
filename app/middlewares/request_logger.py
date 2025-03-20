# app/middlewares/request_logger.py
# Middleware to log every incoming request and its corresponding response

from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger("request_logger")


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Log the incoming request method and URL
        logger.info(f"Incoming request: {request.method} {request.url}")
        response = await call_next(request)
        # Log the response status code
        logger.info(f"Response status: {response.status_code}")
        return response
