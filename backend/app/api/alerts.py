from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models import Alert
from app.services.alert_service import generate_alerts, update_alert_status
from app.schemas.pagination import pagination_params

router = APIRouter(prefix="/alerts", tags=["Alerts"], dependencies=[Depends(require_role("VIEWER"))])


class StatusUpdate(BaseModel):
    status: str


def _serialize(a: Alert) -> dict:
    return {
        "id": a.id,
        "metric_name": a.metric_name,
        "severity": a.severity,
        "status": a.status,
        "observed_value": float(a.observed_value),
        "expected_value": float(a.expected_value) if a.expected_value is not None else None,
        "explanation": a.explanation,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
    }


@router.post("/generate", dependencies=[Depends(require_role("ANALYST"))])
async def trigger_alert_generation(db: Session = Depends(get_db)):
    return generate_alerts(db)


@router.get("/")
async def list_alerts(
    status: str | None = Query(None, description="OPEN, ACKNOWLEDGED or RESOLVED"),
    db: Session = Depends(get_db),
    page=Depends(pagination_params),
):
    query = db.query(Alert)
    if status:
        query = query.filter(Alert.status == status.upper())

    total = query.count()
    results = (
        query.order_by(Alert.created_at.desc(), Alert.id.desc())
        .offset(page["offset"]).limit(page["limit"])
        .all()
    )
    return {
        "total": total,
        "limit": page["limit"],
        "offset": page["offset"],
        "items": [_serialize(a) for a in results],
    }


@router.patch("/{alert_id}/status", dependencies=[Depends(require_role("ANALYST"))])
async def change_alert_status(alert_id: int, body: StatusUpdate, db: Session = Depends(get_db)):
    try:
        alert = update_alert_status(db, alert_id, body.status)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _serialize(alert)