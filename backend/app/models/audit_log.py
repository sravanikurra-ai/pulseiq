from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.db.base import Base


class AuditLog(Base):
    """
    Records security-relevant actions: logins, failed logins, role changes,
    admin operations (Section 26/42 of the blueprint). Never store
    passwords/secrets here — only WHAT happened, WHO did it, WHEN.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # nullable: failed logins may have no known user
    action = Column(String(100), nullable=False, index=True)  # "login_success", "login_failed", "role_changed", etc.
    details = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)