"""
Attaches a short, unique request ID to every incoming request, available
both in logs (via contextvars, so every log line during this request can
include it) and in the response headers (so a user/frontend can report it
back to us for fast debugging).
"""
import uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = uuid.uuid4().hex[:12]
        request_id_var.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response