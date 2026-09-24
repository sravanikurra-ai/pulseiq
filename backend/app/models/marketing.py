from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class MarketingCampaign(Base):
    __tablename__ = "marketing_campaigns"

    id = Column(Integer, primary_key=True)
    external_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    channel = Column(String(100), nullable=False, index=True)  # e.g., "facebook_ads", "google_ads"

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    spend_entries = relationship("MarketingSpend", back_populates="campaign")


class MarketingSpend(Base):
    """
    Periodic (typically daily) spend against a campaign.
    Kept separate from MarketingCampaign because spend is a time series
    (many rows per campaign), while a campaign itself is a single record.
    """
    __tablename__ = "marketing_spend"

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("marketing_campaigns.id"), nullable=False)
    spend_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)

    campaign = relationship("MarketingCampaign", back_populates="spend_entries")