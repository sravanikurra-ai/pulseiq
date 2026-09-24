from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Role(Base):
    """
    Defines the fixed set of roles used for RBAC (Phase 15).
    Stored as data (not a Python enum) so an admin could theoretically
    add a new role later without a code deployment.
    """
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True, nullable=False)  # ADMIN, ANALYST, VIEWER

    users = relationship("User", back_populates="role")