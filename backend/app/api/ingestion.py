from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.ingestion_service import run_full_ingestion

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


@router.post("/run")
async def trigger_ingestion(db: Session = Depends(get_db)):
    """
    Triggers a full ingestion run across all sources (customers, products,
    orders, marketing). Runs synchronously for now — Phase 25 (background
    processing) will move this to a background job so it doesn't block
    the HTTP request for however long ingestion takes.
    """
    results = run_full_ingestion(db)
    return {
        source: {
            "status": log.status,
            "records_fetched": log.records_fetched,
            "records_ingested": log.records_ingested,
        }
        for source, log in results.items()
    }


@router.get("/status")
async def ingestion_status(db: Session = Depends(get_db)):
    """
    Returns the most recent ingestion log per source, so a user/admin can
    check "when did each source last run, and did it succeed?"
    """
    from app.models import DataIngestionLog

    sources = ["customers", "products", "orders", "marketing"]
    status = {}
    for source in sources:
        last_log = (
            db.query(DataIngestionLog)
            .filter(DataIngestionLog.source == source)
            .order_by(DataIngestionLog.started_at.desc())
            .first()
        )
        if last_log:
            status[source] = {
                "status": last_log.status,
                "records_fetched": last_log.records_fetched,
                "records_ingested": last_log.records_ingested,
                "started_at": last_log.started_at.isoformat() if last_log.started_at else None,
                "finished_at": last_log.finished_at.isoformat() if last_log.finished_at else None,
            }
        else:
            status[source] = {"status": "never_run"}
    return status