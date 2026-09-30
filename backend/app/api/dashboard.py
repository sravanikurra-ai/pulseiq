from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models import Anomaly, Forecast, Alert
from app.services import kpi_engine

router = APIRouter(prefix="/dashboard", tags=["Dashboard"], dependencies=[Depends(require_role("VIEWER"))])


@router.get("/summary")
async def dashboard_summary(db: Session = Depends(get_db)):
    """
    One call for the whole dashboard landing page: current-period KPIs,
    open alert counts by severity, and the most recent anomaly/forecast.
    """
    end = date.today()
    start = end - timedelta(days=29)
    kpis = kpi_engine.compute_all_kpis(db, start, end)

    open_alerts = db.query(Alert).filter(Alert.status == "OPEN").all()
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for a in open_alerts:
        if a.severity in severity_counts:
            severity_counts[a.severity] += 1

    latest_anomaly = db.query(Anomaly).order_by(Anomaly.detected_at.desc()).first()
    latest_forecast = db.query(Forecast).order_by(Forecast.forecast_date.asc()).first()

    return {
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "kpis": kpis,
        "open_alerts": {"total": len(open_alerts), "by_severity": severity_counts},
        "latest_anomaly": {
            "date": latest_anomaly.detected_at.date().isoformat(),
            "explanation": latest_anomaly.explanation,
        } if latest_anomaly else None,
        "next_forecast": {
            "date": latest_forecast.forecast_date.isoformat(),
            "predicted_value": float(latest_forecast.predicted_value),
        } if latest_forecast else None,
    }