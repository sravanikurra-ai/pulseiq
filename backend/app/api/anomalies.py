from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.anomaly_service import detect_anomalies
from app.models import Anomaly
from app.api.deps import require_role

router = APIRouter(prefix="/anomalies", tags=["Anomalies"], dependencies=[Depends(require_role("VIEWER"))])


@router.post("/run", dependencies=[Depends(require_role("ANALYST"))])
async def trigger_anomaly_detection(db: Session = Depends(get_db)):
    """
    Runs Isolation Forest anomaly detection over the full daily order
    history in fact_orders_daily, storing results in the anomalies table.
    """
    return detect_anomalies(db)


@router.get("/")
async def list_anomalies(db: Session = Depends(get_db)):
    """Returns all stored anomalies, most recent first."""
    results = db.query(Anomaly).order_by(Anomaly.detected_at.desc()).all()
    return [
        {
            "id": a.id,
            "metric_name": a.metric_name,
            "observed_value": float(a.observed_value),
            "expected_value": float(a.expected_value) if a.expected_value is not None else None,
            "anomaly_score": float(a.anomaly_score),
            "detected_at": a.detected_at.isoformat(),
            "explanation": a.explanation,
        }
        for a in results
    ]