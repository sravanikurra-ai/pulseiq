from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text
from sqlalchemy.sql import func

from app.db.base import Base


class Anomaly(Base):
    """
    An ML-flagged anomaly (Phase 11). Kept deliberately generic (metric_name
    + observed/expected values) so it can represent a revenue anomaly, an
    order-volume anomaly, or a marketing-spend anomaly without needing
    separate tables for each.
    """
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True)
    metric_name = Column(String(100), nullable=False, index=True)
    dimension = Column(String(100), nullable=True)  # e.g., "region:US" — what slice of data was anomalous
    observed_value = Column(Numeric(14, 4), nullable=False)
    expected_value = Column(Numeric(14, 4), nullable=True)
    anomaly_score = Column(Numeric(6, 4), nullable=False)  # raw Isolation Forest score
    detected_at = Column(DateTime(timezone=True), nullable=False, index=True)
    explanation = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())