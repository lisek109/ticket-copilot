from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_ticket_and_classify():
    # Create a ticket
    payload = {
        "channel": "email",
        "subject": "VPN does not work",
        "body": "Hi, I cannot login to VPN since morning. Please help."
    }
    r = client.post("/tickets", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    ticket_id = data["id"]

    # Classify the ticket
    r2 = client.post(f"/tickets/{ticket_id}/classify")
    assert r2.status_code == 200
    pred = r2.json()
    assert pred["category"] in ["access", "incident", "billing", "general"]
    assert 1 <= pred["priority"] <= 4
    assert 0.0 <= pred["confidence"] <= 1.0
    assert pred["model_version"] == "rules-v0"

def test_get_missing_ticket_returns_404():
    r = client.get("/tickets/does-not-exist")
    assert r.status_code == 404
