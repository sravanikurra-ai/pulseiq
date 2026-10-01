"""
Authentication tests covering Phase 14's actual guarantees: public
registration is always VIEWER, duplicates are rejected, wrong password
is rejected, and protected endpoints require a valid token.
"""

def test_registration_ignores_role_escalation_attempt(client):
    response = client.post("/auth/register", json={
        "email": "escalate@example.com", "password": "Password123",
        "full_name": "Attempted Admin", "role": "ADMIN",  # must be ignored
    })
    assert response.status_code == 201
    assert response.json()["role"] == "VIEWER"


def test_duplicate_registration_returns_409(client, registered_viewer):
    response = client.post("/auth/register", json={
        "email": registered_viewer["email"], "password": "Password123",
    })
    assert response.status_code == 409


def test_wrong_password_returns_401(client, registered_viewer):
    response = client.post("/auth/login", data={
        "username": registered_viewer["email"], "password": "WrongPassword",
    })
    assert response.status_code == 401


def test_correct_login_returns_working_token(client, viewer_token):
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {viewer_token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "viewer@example.com"


def test_protected_endpoint_without_token_returns_401(client):
    response = client.get("/auth/me")
    assert response.status_code == 401