from fastapi.testclient import TestClient
from app.main import app

client_local = TestClient(app)

def create_user_and_token(email: str = "testuser@example.com"):
    register_payload = {
        "email": email,
        "password": "StrongPassword123",
        "full_name": "Test User",
    }
    client_local.post("/auth/register", json=register_payload)

    login_payload = {
        "email": email,
        "password": "StrongPassword123",
    }
    response = client_local.post("/auth/login", json=login_payload)
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}




def test_register_and_login(client):
    register_payload = {
        "email": "user1@example.com",
        "password": "StrongPassword123",
        "full_name": "User One",
    }

    r = client.post("/auth/register", json=register_payload)
    assert r.status_code == 200

    data = r.json()
    assert data["email"] == "user1@example.com"

    login_payload = {
        "email": "user1@example.com",
        "password": "StrongPassword123",
    }

    r2 = client.post("/auth/login", json=login_payload)
    assert r2.status_code == 200

    token_data = r2.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_authenticated_user_can_create_ticket(client, auth_headers):
    headers = auth_headers(email="user2@example.com")

    payload = {
        "channel": "email",
        "subject": "VPN issue",
        "body": "I cannot login to VPN.",
    }

    r = client.post("/tickets", json=payload, headers=headers)
    assert r.status_code == 200

    data = r.json()
    assert data["subject"] == "VPN issue"
    assert data["owner_id"] is not None


def test_user_cannot_access_another_users_ticket(client):
    headers_user1 = create_user_and_token("usera@example.com")
    headers_user2 = create_user_and_token("userb@example.com")

    payload = {
        "channel": "email",
        "subject": "Private ticket",
        "body": "Only owner should see this."
    }

    r = client.post("/tickets", json=payload, headers=headers_user1)
    ticket_id = r.json()["id"]

    r2 = client.get(f"/tickets/{ticket_id}", headers=headers_user2)
    assert r2.status_code == 403
    
    
def test_create_ticket_requires_auth(client):
    payload = {
        "channel": "email",
        "subject": "VPN issue",
        "body": "Cannot login."
    }

    r = client.post("/tickets", json=payload)
    assert r.status_code in [401, 403]


