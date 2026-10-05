from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import create_access_token
from app.db.session import get_db
from app.models import User
from app.schemas.auth import UserCreate, UserOut
from app.services.auth_service import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["Auth"])


def _to_out(user: User) -> UserOut:
    return UserOut(id=user.id, email=user.email, full_name=user.full_name,
                   role=user.role.name, is_active=user.is_active)


# Plain `def` (not `async def`): bcrypt is deliberately slow, and FastAPI runs
# plain functions in a thread pool so they don't block the event loop.
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: UserCreate, db: Session = Depends(get_db)):
    try:
        user = register_user(db, body.email, body.password, body.full_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return _to_out(user)


@router.post("/login")
@limiter.limit("5/minute")
def login(
    request: Request, response: Response,
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db),
):
    """
    OAuth2 forms call the field "username"; we use it for the email.
    On success, sets the JWT as an httpOnly cookie rather than returning
    it in the JSON body — client-side JavaScript can never read it, which
    closes the XSS token-theft risk that localStorage-based auth has.

    samesite="lax" (not "strict"): strict same-site matching can fail
    cross-port even on the same machine depending on browser/client
    behavior — lax still blocks genuine cross-site POST forgery while
    working reliably for this single-origin-family local SPA setup.
    """
    user = authenticate_user(db, form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user.id)
    response.set_cookie(
        key="pulseiq_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.app_env == "production",
        max_age=settings.access_token_expire_minutes * 60,
    )
    return {"message": "Logged in successfully"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("pulseiq_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return _to_out(current_user)