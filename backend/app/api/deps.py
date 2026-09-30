from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Dependency: any endpoint that lists this becomes protected."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_error
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise credentials_error

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_error
    return user
import logging

logger = logging.getLogger(__name__)

# Higher number = more privilege. ADMIN inherits ANALYST, which inherits VIEWER.
ROLE_RANK = {"VIEWER": 1, "ANALYST": 2, "ADMIN": 3}


def require_role(minimum_role: str):
    """
    Returns a dependency that allows the request only if the caller's role
    is at least `minimum_role`. Returns 401 if not logged in (from
    get_current_user) and 403 if logged in but not permitted.
    """
    if minimum_role not in ROLE_RANK:
        raise ValueError(f"Unknown role: {minimum_role}")

    def checker(current_user: User = Depends(get_current_user)) -> User:
        user_rank = ROLE_RANK.get(current_user.role.name, 0)
        if user_rank < ROLE_RANK[minimum_role]:
            logger.warning(
                f"Access denied: user_id={current_user.id} role={current_user.role.name} "
                f"required>={minimum_role}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return checker