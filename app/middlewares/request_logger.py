# app/middlewares/request_logger.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from uuid import uuid4
from app.utils.logger import get_logger

logger = get_logger("request_logger")


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid4())
        client_ip = request.client.host if request.client else "unknown"
        logger.info(
            f"[{request_id}] Incoming request: {request.method} {request.url} from {client_ip}"
        )
        response = await call_next(request)
        logger.info(f"[{request_id}] Response status: {response.status_code}")
        # Optionally add request_id in response header for tracing
        response.headers["X-Request-ID"] = request_id
        return response
