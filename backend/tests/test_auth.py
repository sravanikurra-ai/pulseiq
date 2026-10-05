"""
Authentication tests covering Phase 14's actual guarantees: public
registration is always VIEWER, duplicates are rejected, wrong password
is rejected, and protected endpoints require a valid session. Updated in
Phase 21 for cookie-based auth instead of bearer tokens.
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


def test_correct_login_returns_working_session(logged_in_viewer):
    response = logged_in_viewer.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "viewer@example.com"


def test_protected_endpoint_without_login_returns_401(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_logout_clears_session(logged_in_viewer):
    me_before = logged_in_viewer.get("/auth/me")
    assert me_before.status_code == 200

    logout_response = logged_in_viewer.post("/auth/logout")
    assert logout_response.status_code == 200

    me_after = logged_in_viewer.get("/auth/me")
    assert me_after.status_code == 401