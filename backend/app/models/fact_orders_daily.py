from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Index
from sqlalchemy.sql import func

from app.db.base import Base


class FactOrdersDaily(Base):
    """
    A derived, pre-aggregated 'fact table': one row per
    (order_date, region, channel, status) combination, with revenue and
    order-count already summed. This is what the KPI engine (Phase 10)
    queries, instead of aggregating raw orders on every request.

    Rebuilt by the ETL pipeline (etl_service.py) — never written to
    directly by ingestion or the API.
    """
    __tablename__ = "fact_orders_daily"

    id = Column(Integer, primary_key=True)

    order_date = Column(Date, nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False)
    week = Column(Integer, nullable=False)
    day_of_week = Column(String(10), nullable=False)  # "Monday", "Tuesday", etc.

    region = Column(String(100), nullable=True, index=True)
    channel = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, index=True)

    order_count = Column(Integer, nullable=False, default=0)
    total_revenue = Column(Numeric(14, 2), nullable=False, default=0)
    total_quantity = Column(Integer, nullable=False, default=0)

    computed_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_fact_orders_daily_date_region_channel_status", "order_date", "region", "channel", "status"),
    )