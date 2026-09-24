from sqlalchemy import Column, Integer, String, Numeric

from app.db.base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    external_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True, index=True)  # used for "which product has unusual sales" queries
    unit_price = Column(Numeric(10, 2), nullable=False)