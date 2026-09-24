from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from app.db.base import Base


class DataIngestionLog(Base):
    """
    One row per ingestion run. This is our audit trail for "what data came
    in, from where, and did it succeed" — critical for debugging data issues.
    """
    __tablename__ = "data_ingestion_logs"

    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False, index=True)  # "orders", "crm", "marketing"
    status = Column(String(20), nullable=False)  # "success", "partial", "failed"
    records_fetched = Column(Integer, default=0)
    records_ingested = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)


class DataQualityResult(Base):
    """
    Measurable data-quality metrics for one ingestion run (Section 13 of
    the blueprint) — valid/invalid/duplicate/missing counts.
    """
    __tablename__ = "data_quality_results"

    id = Column(Integer, primary_key=True)
    ingestion_log_id = Column(Integer, nullable=False, index=True)  # loose FK-style reference, see note below
    valid_records = Column(Integer, default=0)
    invalid_records = Column(Integer, default=0)
    duplicate_records = Column(Integer, default=0)
    missing_value_records = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())