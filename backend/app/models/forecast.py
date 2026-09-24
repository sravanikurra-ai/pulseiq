from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime
from sqlalchemy.sql import func

from app.db.base import Base


class Forecast(Base):
    """
    An ML-generated forecast (Phase 12) for a future period, with a
    confidence range and the evaluation metric of the model that produced it.
    """
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True)
    metric_name = Column(String(100), nullable=False, index=True)
    forecast_date = Column(Date, nullable=False, index=True)  # the future date being predicted
    predicted_value = Column(Numeric(14, 4), nullable=False)
    lower_bound = Column(Numeric(14, 4), nullable=True)
    upper_bound = Column(Numeric(14, 4), nullable=True)
    model_name = Column(String(100), nullable=False)  # e.g., "exponential_smoothing"
    mae = Column(Numeric(14, 4), nullable=True)  # evaluation metric recorded at training time

    created_at = Column(DateTime(timezone=True), server_default=func.now())