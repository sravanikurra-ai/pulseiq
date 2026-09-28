import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import DUMMY_HASH, hash_password, verify_password
from app.models import AuditLog, Role, User

logger = logging.getLogger(__name__)


def _audit(db: Session, action: str, user_id: int | None = None, details: str | None = None) -> None:
    """Never pass passwords or tokens in `details`."""
    db.add(AuditLog(user_id=user_id, action=action, details=(details or "")[:500] or None))
    db.commit()


def register_user(db: Session, email: str, password: str, full_name: str | None) -> User:
    email = email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise ValueError("Email already registered")

    viewer_role = db.query(Role).filter(Role.name == "VIEWER").first()
    if viewer_role is None:
        raise RuntimeError("Roles are not seeded. Run: python -m scripts.create_admin")

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role_id=viewer_role.id,  # public registration is always VIEWER
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # two simultaneous registrations for one email
        db.rollback()
        raise ValueError("Email already registered")
    db.refresh(user)
    _audit(db, "user_registered", user_id=user.id)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    email = email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if user is None:
        verify_password(password, DUMMY_HASH)  # equalize timing
        _audit(db, "login_failed", details=f"unknown email: {email}")
        return None
    if not verify_password(password, user.hashed_password):
        _audit(db, "login_failed", user_id=user.id, details="wrong password")
        return None
    if not user.is_active:
        _audit(db, "login_failed", user_id=user.id, details="inactive account")
        return None

    _audit(db, "login_success", user_id=user.id)
    return user