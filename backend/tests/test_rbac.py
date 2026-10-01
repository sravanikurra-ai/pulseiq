"""
RBAC tests: the exact scenarios from Section 30 of the blueprint —
"unauthorized endpoint" and "viewer trying to perform admin operation".
"""
def test_viewer_cannot_trigger_ingestion(client, viewer_token):
    response = client.post("/ingestion/run", headers={"Authorization": f"Bearer {viewer_token}"})
    assert response.status_code == 403


def test_admin_can_trigger_ingestion(client, admin_token):
    """Confirms 403 above is a real role check, not the endpoint being broken for everyone."""
    response = client.post("/ingestion/run", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200


def test_viewer_can_read_kpis(client, viewer_token):
    response = client.get("/kpis/summary", headers={"Authorization": f"Bearer {viewer_token}"})
    assert response.status_code == 200


def test_unauthenticated_request_returns_401_not_403(client):
    """A missing token must be 401 (not authenticated), distinct from 403 (authenticated but forbidden)."""
    response = client.get("/kpis/summary")
    assert response.status_code == 401