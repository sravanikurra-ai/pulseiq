from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Order(Base):
    """
    The core revenue-generating record. Every KPI (revenue, AOV, conversion)
    is ultimately derived from this table.
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    external_id = Column(String(100), unique=True, nullable=False, index=True)

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    quantity = Column(Integer, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), nullable=False, default="completed")  # completed, cancelled, refunded
    region = Column(String(100), nullable=True, index=True)
    channel = Column(String(100), nullable=True)  # e.g., "web", "mobile_app"

    order_date = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer", back_populates="orders")
    product = relationship("Product")

    __table_args__ = (
        Index("ix_orders_date_status", "order_date", "status"),
    )