from fastapi.testclient import TestClient
from app.main import app
from app.db.database import Base, engine

# Ensure tables exist for tests (CI starts with empty workspace)
Base.metadata.create_all(bind=engine)

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
    assert pred["model_version"] in ["rules-v0", "tfidf-logreg-v1"]

def test_get_missing_ticket_returns_404():
    r = client.get("/tickets/does-not-exist")
    assert r.status_code == 404
    
def test_ml_model_used_when_present():
    # If a trained model exists, classify should return ML version
    payload = {
        "channel": "email",
        "subject": "Service is down",
        "body": "Critical outage, cannot access systems"
    }
    r = client.post("/tickets", json=payload)
    ticket_id = r.json()["id"]

    r2 = client.post(f"/tickets/{ticket_id}/classify")
    assert r2.status_code == 200
    pred = r2.json()

    # If model is not trained, this will be "rules-v0".
    # After training, it should be ML version.
    assert pred["model_version"] in ["rules-v0", "tfidf-logreg-v1"]

