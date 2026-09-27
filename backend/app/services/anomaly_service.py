"""
Anomaly detection service using Isolation Forest (Phase 11).

WHAT PROBLEM THIS SOLVES: flags days where order volume/revenue/quantity
look meaningfully different from the surrounding pattern, without relying
on a fixed, brittle threshold.

WHY TRADITIONAL PROGRAMMING ISN'T ENOUGH: "normal" isn't a single fixed
number — it varies with trend and day-to-day variation. A hardcoded rule
like "orders < 20 is bad" would misfire constantly as the business grows
or as weekday/weekend patterns shift. ML learns the shape of "normal"
directly from the data.

ALGORITHM: Isolation Forest (unsupervised). Chosen because it needs no
labeled anomaly data (real anomalies are rare and expensive to label by
hand), handles multiple features naturally, and is fast/simple enough to
explain and defend in an interview.
"""
import logging
from datetime import date, datetime, timezone
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func

from app.models import FactOrdersDaily, Anomaly

logger = logging.getLogger(__name__)

CONTAMINATION = 0.05  # we expect ~5% of days to be genuinely anomalous


def _load_daily_metrics(db: Session) -> pd.DataFrame:
    """
    INPUT: aggregates fact_orders_daily (which is already split by region/
    channel/status) up to ONE row per calendar day, summing across all
    dimensions — since we're detecting anomalies at the whole-business
    level first, not per-region (that's a reasonable, documented scope
    choice; per-dimension anomaly detection is a natural future extension).
    """
    rows = (
        db.query(
            FactOrdersDaily.order_date,
            sql_func.sum(FactOrdersDaily.order_count).label("order_count"),
            sql_func.sum(FactOrdersDaily.total_revenue).label("total_revenue"),
            sql_func.sum(FactOrdersDaily.total_quantity).label("total_quantity"),
        )
        .filter(FactOrdersDaily.status == "completed")
        .group_by(FactOrdersDaily.order_date)
        .order_by(FactOrdersDaily.order_date)
        .all()
    )
    df = pd.DataFrame(rows, columns=["order_date", "order_count", "total_revenue", "total_quantity"])
    df["total_revenue"] = df["total_revenue"].astype(float)
    return df


def detect_anomalies(db: Session) -> dict:
    """
    PREPROCESSING: standardize features (mean 0, std 1) so revenue
    (thousands) doesn't dominate order_count (tens) purely due to scale.

    TRAINING + INFERENCE: Isolation Forest is fit and applied to the same
    dataset in one step (fit_predict) — appropriate here since we're doing
    a full historical scan, not real-time streaming inference. A production
    system might instead persist a trained model and re-use it for new
    incoming days; we note this as a future enhancement.

    OUTPUT: for each flagged day, an anomaly_score (raw IF decision_function
    output — more negative means more anomalous) and a human-readable
    explanation comparing observed vs. expected (mean) values.
    """
    df = _load_daily_metrics(db)

    if len(df) < 10:
        logger.warning("Not enough data points for meaningful anomaly detection (need >= 10 days).")
        return {"status": "skipped", "reason": "insufficient_data", "rows_available": len(df)}

    features = df[["order_count", "total_revenue", "total_quantity"]]
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    model = IsolationForest(
        contamination=CONTAMINATION,
        random_state=42,  # reproducibility — same run, same results
        n_estimators=100,
    )
    predictions = model.fit_predict(scaled_features)  # -1 = anomaly, 1 = normal
    scores = model.decision_function(scaled_features)  # continuous anomaly score

    df["is_anomaly"] = predictions == -1
    df["anomaly_score"] = scores

    mean_order_count = float(df["order_count"].mean())
    mean_revenue = float(df["total_revenue"].mean())

    anomalies_found = []
    for _, row in df[df["is_anomaly"]].iterrows():
        direction = "below" if row["order_count"] < mean_order_count else "above"
        explanation = (
            f"Order count ({int(row['order_count'])}) is {direction} the typical daily average "
            f"({mean_order_count:.1f}). Revenue on this day was {row['total_revenue']:.2f} "
            f"vs. a typical {mean_revenue:.2f}."
        )

        anomaly = Anomaly(
            metric_name="daily_orders",
            dimension=None,
            observed_value=float(row["order_count"]),
            expected_value=round(mean_order_count, 2),
            anomaly_score=round(float(row["anomaly_score"]), 4),
            detected_at=datetime.combine(row["order_date"], datetime.min.time()).replace(tzinfo=timezone.utc),
            explanation=explanation,
        )
        db.add(anomaly)
        anomalies_found.append({
            "date": row["order_date"].isoformat(),
            "order_count": int(row["order_count"]),
            "total_revenue": float(row["total_revenue"]),
            "anomaly_score": round(float(row["anomaly_score"]), 4),
            "explanation": explanation,
        })

    db.commit()
    logger.info(f"Anomaly detection: scanned {len(df)} days, flagged {len(anomalies_found)} anomalies.")

    return {
        "status": "success",
        "days_scanned": len(df),
        "anomalies_found": len(anomalies_found),
        "contamination_setting": CONTAMINATION,
        "anomalies": anomalies_found,
    }