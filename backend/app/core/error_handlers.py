"""
Centralized exception handling (Phase 20). Every unhandled exception in the
app passes through here exactly once, so logging and the client-facing
error shape are consistent everywhere — not re-implemented per endpoint.
"""
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.middleware.request_id import request_id_var

logger = logging.getLogger(__name__)


def _error_body(detail: str) -> dict:
    return {"detail": detail, "request_id": request_id_var.get()}


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handles our own intentional HTTPException raises (401, 403, 404, 409,
    etc. — the ones we explicitly raise in auth.py, alerts.py, etc.).
    These are expected, known error cases, so we log at INFO, not ERROR.
    """
    logger.info(
        f"HTTP {exc.status_code} on {request.method} {request.url.path} "
        f"[request_id={request_id_var.get()}]: {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.detail),
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handles Pydantic/FastAPI request validation failures (422) — e.g. a
    missing required field, a malformed email. These are client mistakes,
    not server bugs, so INFO level, and we pass through Pydantic's actual
    field-level errors since they're genuinely useful to the API caller.
    """
    logger.info(
        f"Validation error on {request.method} {request.url.path} "
        f"[request_id={request_id_var.get()}]: {exc.errors()}"
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "request_id": request_id_var.get()},
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    The final safety net: anything we didn't anticipate (a bug, a DB
    connection drop, an unexpected None) lands here. This is the ONE place
    that decides what a client ever sees for a genuine server crash.
    """
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path} "
        f"[request_id={request_id_var.get()}]: {exc!r}",
        exc_info=True,  # logs the FULL traceback server-side, always
    )
    detail = str(exc) if settings.debug else "An internal error occurred. Please try again or contact support."
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_body(detail),
    )