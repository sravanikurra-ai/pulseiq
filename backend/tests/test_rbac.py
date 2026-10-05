"""
RBAC tests: the exact scenarios from Section 30 of the blueprint —
"unauthorized endpoint" and "viewer trying to perform admin operation".
Updated in Phase 21 for cookie-based auth instead of bearer tokens.
"""
def test_viewer_cannot_trigger_ingestion(logged_in_viewer):
    response = logged_in_viewer.post("/ingestion/run")
    assert response.status_code == 403


def test_admin_can_trigger_ingestion(logged_in_admin):
    """Confirms 403 above is a real role check, not the endpoint being broken for everyone."""
    response = logged_in_admin.post("/ingestion/run")
    assert response.status_code == 200


def test_viewer_can_read_kpis(logged_in_viewer):
    response = logged_in_viewer.get("/kpis/summary")
    assert response.status_code == 200


def test_unauthenticated_request_returns_401_not_403(client):
    """A missing session must be 401 (not authenticated), distinct from 403 (authenticated but forbidden)."""
    response = client.get("/kpis/summary")
    assert response.status_code == 401