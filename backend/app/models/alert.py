from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text
from sqlalchemy.sql import func

from app.db.base import Base


class Alert(Base):
    """
    An actionable notification generated from an anomaly or forecast
    deviation (Phase 13). Has a lifecycle: OPEN -> ACKNOWLEDGED -> RESOLVED.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    metric_name = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False)  # "low", "medium", "high", "critical"
    status = Column(String(20), nullable=False, default="OPEN", index=True)  # OPEN, ACKNOWLEDGED, RESOLVED
    observed_value = Column(Numeric(14, 4), nullable=False)
    expected_value = Column(Numeric(14, 4), nullable=True)
    explanation = Column(Text, nullable=True)

    source_anomaly_id = Column(Integer, nullable=True)
    source_forecast_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)