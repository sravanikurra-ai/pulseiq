"""
Alert service (Phase 13): converts anomalies and forecast deviations
into actionable alerts with severity and a status lifecycle.

Design rules:
- Severity is derived from the anomaly score using fixed thresholds.
- Generation is idempotent via a stable dedup_key (metric + date),
  because anomaly IDs change every time detection is re-run.
- Existing alerts are never modified or deleted by generation, so a
  person's ACKNOWLEDGED/RESOLVED work is preserved.
"""
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models import Alert, Anomaly, Forecast, FactOrdersDaily
from sqlalchemy import func as sql_func

logger = logging.getLogger(__name__)

VALID_STATUSES = {"OPEN", "ACKNOWLEDGED", "RESOLVED"}
ALLOWED_TRANSITIONS = {
    "OPEN": {"ACKNOWLEDGED", "RESOLVED"},
    "ACKNOWLEDGED": {"RESOLVED"},
    "RESOLVED": set(),
}


def severity_from_score(score: float) -> str:
    """Fixed thresholds, calibrated on our synthetic data (see README)."""
    if score <= -0.25:
        return "critical"
    if score <= -0.15:
        return "high"
    if score <= -0.05:
        return "medium"
    return "low"


def generate_alerts(db: Session) -> dict:
    created = 0
    skipped_existing = 0

    # --- 1. Alerts from anomalies ---
    anomalies = db.query(Anomaly).all()
    existing_keys = {k for (k,) in db.query(Alert.dedup_key).filter(Alert.dedup_key.isnot(None)).all()}

    for a in anomalies:
        key = f"anomaly:{a.metric_name}:{a.detected_at.date().isoformat()}"
        if key in existing_keys:
            skipped_existing += 1
            continue

        score = float(a.anomaly_score)
        db.add(Alert(
            metric_name=a.metric_name,
            severity=severity_from_score(score),
            status="OPEN",
            observed_value=a.observed_value,
            expected_value=a.expected_value,
            explanation=a.explanation,
            source_anomaly_id=a.id,
            dedup_key=key,
        ))
        existing_keys.add(key)
        created += 1

    # --- 2. Forecast deviation alert (latest actual day vs stored forecast) ---
    forecast_status = "skipped: no stored forecast covers the latest actual day"
    latest = (
        db.query(
            FactOrdersDaily.order_date,
            sql_func.sum(FactOrdersDaily.total_revenue).label("rev"),
        )
        .filter(FactOrdersDaily.status == "completed")
        .group_by(FactOrdersDaily.order_date)
        .order_by(FactOrdersDaily.order_date.desc())
        .first()
    )
    if latest:
        fc = db.query(Forecast).filter(
            Forecast.metric_name == "daily_revenue",
            Forecast.forecast_date == latest.order_date,
        ).first()
        if fc and fc.lower_bound is not None and fc.upper_bound is not None:
            actual = float(latest.rev)
            forecast_status = "checked: within forecast range"
            if actual < float(fc.lower_bound) or actual > float(fc.upper_bound):
                key = f"forecast:daily_revenue:{latest.order_date.isoformat()}"
                if key not in existing_keys:
                    direction = "below" if actual < float(fc.lower_bound) else "above"
                    db.add(Alert(
                        metric_name="daily_revenue",
                        severity="high",
                        status="OPEN",
                        observed_value=actual,
                        expected_value=fc.predicted_value,
                        explanation=(
                            f"Actual revenue {actual:.2f} was {direction} the forecast range "
                            f"[{float(fc.lower_bound):.2f}, {float(fc.upper_bound):.2f}]."
                        ),
                        source_forecast_id=fc.id,
                        dedup_key=key,
                    ))
                    created += 1
                    forecast_status = "alert created: outside forecast range"

    db.commit()
    logger.info(f"Alert generation: created={created}, skipped_existing={skipped_existing}")
    return {
        "status": "success",
        "alerts_created": created,
        "already_existing": skipped_existing,
        "forecast_check": forecast_status,
    }


def update_alert_status(db: Session, alert_id: int, new_status: str) -> Alert:
    new_status = new_status.upper()
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{new_status}'. Allowed: {sorted(VALID_STATUSES)}")

    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert is None:
        raise LookupError(f"Alert {alert_id} not found")

    if new_status not in ALLOWED_TRANSITIONS[alert.status]:
        raise ValueError(f"Cannot move alert from {alert.status} to {new_status}")

    alert.status = new_status
    if new_status == "RESOLVED":
        alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert