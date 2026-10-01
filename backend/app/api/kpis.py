from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import kpi_engine
from app.api.deps import require_role

router = APIRouter(prefix="/kpis", tags=["KPIs"], dependencies=[Depends(require_role("VIEWER"))])


def _default_period():
    """Defaults to the last 30 days if the caller doesn't specify a period."""
    end = date.today()
    start = end - timedelta(days=29)
    return start, end


@router.get("/revenue")
async def get_revenue(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    start, end = (start_date, end_date) if start_date and end_date else _default_period()
    return {"kpi": "revenue", "period_start": start, "period_end": end, "value": kpi_engine.calculate_revenue(db, start, end)}


@router.get("/orders")
async def get_orders(
    start_date: date | None = Query(None), end_date: date | None = Query(None), db: Session = Depends(get_db)
):
    start, end = (start_date, end_date) if start_date and end_date else _default_period()
    return {"kpi": "orders", "period_start": start, "period_end": end, "value": kpi_engine.calculate_orders(db, start, end)}


@router.get("/aov")
async def get_aov(
    start_date: date | None = Query(None), end_date: date | None = Query(None), db: Session = Depends(get_db)
):
    start, end = (start_date, end_date) if start_date and end_date else _default_period()
    return {"kpi": "aov", "period_start": start, "period_end": end, "value": kpi_engine.calculate_aov(db, start, end)}


@router.get("/conversion")
async def get_conversion(
    start_date: date | None = Query(None), end_date: date | None = Query(None), db: Session = Depends(get_db)
):
    start, end = (start_date, end_date) if start_date and end_date else _default_period()
    return {
        "kpi": "conversion_rate", "period_start": start, "period_end": end,
        "value": kpi_engine.calculate_conversion_rate(db, start, end),
        "note": kpi_engine.KPI_LIMITATIONS["conversion_rate"],
    }


@router.get("/cac")
async def get_cac(
    start_date: date | None = Query(None), end_date: date | None = Query(None), db: Session = Depends(get_db)
):
    start, end = (start_date, end_date) if start_date and end_date else _default_period()
    return {
        "kpi": "cac", "period_start": start, "period_end": end,
        "value": kpi_engine.calculate_cac(db, start, end),
        "note": kpi_engine.KPI_LIMITATIONS["cac"],
    }


@router.get("/retention")
async def get_retention(
    start_date: date | None = Query(None), end_date: date | None = Query(None), db: Session = Depends(get_db)
):
    start, end = (start_date, end_date) if start_date and end_date else _default_period()
    return {"kpi": "retention_rate", "period_start": start, "period_end": end, "value": kpi_engine.calculate_retention_rate(db, start, end)}


@router.get("/growth")
async def get_growth(
    start_date: date | None = Query(None), end_date: date | None = Query(None), db: Session = Depends(get_db)
):
    start, end = (start_date, end_date) if start_date and end_date else _default_period()
    return {"kpi": "growth_rate", "period_start": start, "period_end": end, "value": kpi_engine.calculate_growth_rate(db, start, end)}


@router.get("/marketing-roi")
async def get_marketing_roi(
    start_date: date | None = Query(None), end_date: date | None = Query(None), db: Session = Depends(get_db)
):
    start, end = (start_date, end_date) if start_date and end_date else _default_period()
    return {
        "kpi": "marketing_roi", "period_start": start, "period_end": end,
        "value": kpi_engine.calculate_marketing_roi(db, start, end),
        "note": kpi_engine.KPI_LIMITATIONS["marketing_roi"],
    }


@router.get("/summary")
async def get_summary(
    start_date: date | None = Query(None), end_date: date | None = Query(None), db: Session = Depends(get_db)
):
    """All KPIs at once, for the dashboard's main summary cards."""
    start, end = (start_date, end_date) if start_date and end_date else _default_period()
    return kpi_engine.compute_all_kpis(db, start, end)

@router.get("/revenue/trend")
async def get_revenue_trend(
    days: int = Query(120, ge=7, le=365), db: Session = Depends(get_db)
):
    return {"items": kpi_engine.get_daily_revenue_trend(db, days)}