import sys
from pathlib import Path

# Add the project root (parent of backend/) to sys.path so app code can
# import from the top-level data/ package, which simulates external
# Orders/CRM/Marketing systems. In production, these mock imports would
# be replaced by real HTTP API calls, and this path shim would be removed.
sys.path.append(str(Path(__file__).resolve().parents[2]))

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.core.limiter import limiter
from app.core.error_handlers import (
    http_exception_handler, validation_exception_handler, unhandled_exception_handler,
)
from app.db.session import get_db
from app.middleware.request_id import RequestIDMiddleware
from app.api import ingestion, etl, kpis, anomalies, forecasts, alerts, auth, dashboard, assistant

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"PulseIQ starting up | env={settings.app_env} | debug={settings.debug}")
    if settings.jwt_secret_key == "changeme":
        logger.warning("JWT_SECRET_KEY is the default 'changeme'. Set a real secret in .env.")
    yield
    logger.info("PulseIQ shutting down")


app = FastAPI(
    title="PulseIQ API",
    description="Real-Time Business Intelligence & Anomaly Detection Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Allow the React frontend (running on a different port) to call this API.
# allow_credentials=True is required for the httpOnly cookie to be sent
# cross-port in development; allow_origins must list explicit origins
# (not "*") since wildcard origins are incompatible with credentialed requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestIDMiddleware)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(ingestion.router)
app.include_router(etl.router)
app.include_router(kpis.router)
app.include_router(anomalies.router)
app.include_router(forecasts.router)
app.include_router(alerts.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(assistant.router)


@app.get("/health", tags=["System"])
async def health_check(db: Session = Depends(get_db)):
    """
    Liveness + readiness check. Confirms the server is running AND
    that it can successfully reach the database.
    """
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok",
        "service": "PulseIQ API",
        "version": "0.1.0",
        "database": db_status,
    }