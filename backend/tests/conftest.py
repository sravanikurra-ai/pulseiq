"""
Shared Pytest fixtures: a clean test database per test, and a FastAPI
TestClient wired to use it instead of the real development database.
"""
import email_validator
email_validator.CHECK_DELIVERABILITY = False
# Test domains like example.com resolve via DNS but intentionally have no
# mail server configured, so email-validator's default deliverability
# check (a live MX lookup) rejects every synthetic test email. This
# disables that check for the test process only — production code in
# app/ never sets this flag, so real email validation is unaffected.

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Role

test_engine = create_engine(settings.test_database_url)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture()
def db_session():
    """
    Fresh schema for every test function: drop everything, recreate,
    seed the 3 roles, yield a session, then clean up. Slower than reusing
    a schema, but guarantees no test can leak state into another.
    """
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    for name in ["ADMIN", "ANALYST", "VIEWER"]:
        session.add(Role(name=name))
    session.commit()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    """TestClient with the real app, but get_db overridden to use the test database."""
    from app.core.limiter import limiter
    limiter.reset()  # clear rate-limit counters between tests, so tests don't compete for the same quota

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def registered_viewer(client):
    """A real registered VIEWER user, via the actual API — not inserted directly."""
    response = client.post("/auth/register", json={
        "email": "viewer@example.com", "password": "Password123", "full_name": "Test Viewer",
    })
    assert response.status_code == 201, f"Setup failed: {response.status_code} {response.text}"
    return {"email": "viewer@example.com", "password": "Password123"}


@pytest.fixture()
def logged_in_viewer(client, registered_viewer):
    """
    Logs in as the viewer. Since auth now uses an httpOnly cookie (Phase 21)
    rather than a bearer token, there's no token to pass around manually —
    TestClient's cookie jar persists the session automatically for every
    subsequent request made with this same client instance, just like a
    real browser. Returns the client itself, now authenticated.
    """
    response = client.post("/auth/login", data={
        "username": registered_viewer["email"], "password": registered_viewer["password"],
    })
    assert response.status_code == 200, f"Login failed: {response.status_code} {response.text}"
    return client


@pytest.fixture()
def logged_in_admin(client, db_session):
    """Creates an admin directly (no public endpoint for this, by design) and logs in."""
    from app.core.security import hash_password
    from app.models import User
    admin_role = db_session.query(Role).filter(Role.name == "ADMIN").first()
    db_session.add(User(
        email="admin@example.com", hashed_password=hash_password("AdminPass123"),
        full_name="Test Admin", role_id=admin_role.id,
    ))
    db_session.commit()
    response = client.post("/auth/login", data={"username": "admin@example.com", "password": "AdminPass123"})
    assert response.status_code == 200, f"Admin login failed: {response.status_code} {response.text}"
    return client