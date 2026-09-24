from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Customer(Base):
    """
    Represents a customer record ingested from the (simulated) CRM system.
    """
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    external_id = Column(String(100), unique=True, nullable=False, index=True)  # ID from the source CRM system
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    region = Column(String(100), nullable=True, index=True)  # used for "which region has declining sales" queries
    acquisition_channel = Column(String(100), nullable=True)  # e.g., "organic", "paid_social" — feeds CAC/ROI calcs

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    orders = relationship("Order", back_populates="customer")