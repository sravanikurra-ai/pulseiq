from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime
from sqlalchemy.sql import func

from app.db.base import Base


class KPIResult(Base):
    """
    Stores computed KPI values per period, so the dashboard doesn't need
    to recompute revenue/AOV/etc. from raw orders on every single request.
    The KPI engine (Phase 10) writes here; the API reads from here.
    """
    __tablename__ = "kpi_results"

    id = Column(Integer, primary_key=True)
    kpi_name = Column(String(100), nullable=False, index=True)  # "revenue", "aov", "conversion_rate", etc.
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False)
    value = Column(Numeric(14, 4), nullable=False)
    dimension = Column(String(100), nullable=True)  # e.g., region="US" — allows KPIs sliced by dimension
    computed_at = Column(DateTime(timezone=True), server_default=func.now())