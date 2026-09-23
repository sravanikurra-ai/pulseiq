from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import configure_logging
import logging

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PulseIQ API",
    description="Real-Time Business Intelligence & Anomaly Detection Platform",
    version="0.1.0",
)

# Allow the future React frontend (running on a different port) to call this API.
# In production this list should be tightened to the real frontend domain only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    logger.info(f"PulseIQ starting up | env={settings.app_env} | debug={settings.debug}")


@app.get("/health", tags=["System"])
async def health_check():
    """
    Basic liveness check. Returns 200 OK if the server process is running.
    Does NOT yet check database/redis connectivity — that comes in Phase 4.
    """
    return {"status": "ok", "service": "PulseIQ API", "version": "0.1.0"}