from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.etl_service import run_etl

router = APIRouter(prefix="/etl", tags=["ETL"])


@router.post("/run")
async def trigger_etl(
    start_date: date | None = Query(None, description="Optional start date (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="Optional end date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Triggers the ETL transform, rebuilding fact_orders_daily for the given
    date range (or the full order history if no range is given).
    """
    return run_etl(db, start_date=start_date, end_date=end_date)