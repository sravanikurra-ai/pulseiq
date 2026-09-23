from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import configure_logging
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

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