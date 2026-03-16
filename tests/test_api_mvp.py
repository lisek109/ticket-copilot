from app.rag import query as rag_query


def test_create_ticket_and_classify(client, auth_headers):
    headers = auth_headers(email="api1@example.com")

    payload = {
        "channel": "email",
        "subject": "VPN does not work",
        "body": "Hi, I cannot login to VPN since morning. Please help.",
    }

    r = client.post("/tickets", json=payload, headers=headers)
    assert r.status_code == 200

    data = r.json()
    assert "id" in data
    ticket_id = data["id"]

    r2 = client.post(f"/tickets/{ticket_id}/classify", headers=headers)
    assert r2.status_code == 200

    pred = r2.json()
    assert pred["category"] in ["access", "incident", "billing", "general"]
    assert 1 <= pred["priority"] <= 4
    assert 0.0 <= pred["confidence"] <= 1.0
    assert pred["model_version"] in ["rules-v0", "tfidf-logreg-v1"]


def test_get_missing_ticket_returns_404(client, auth_headers):
    headers = auth_headers(email="api2@example.com")

    r = client.get("/tickets/does-not-exist", headers=headers)
    assert r.status_code == 404


def test_ml_model_used_when_present(client, auth_headers):
    headers = auth_headers(email="api3@example.com")

    payload = {
        "channel": "email",
        "subject": "Service is down",
        "body": "Critical outage, cannot access systems",
    }

    r = client.post("/tickets", json=payload, headers=headers)
    assert r.status_code == 200

    ticket_id = r.json()["id"]

    r2 = client.post(f"/tickets/{ticket_id}/classify", headers=headers)
    assert r2.status_code == 200

    pred = r2.json()
    assert pred["model_version"] in ["rules-v0", "tfidf-logreg-v1"]


def test_answer_returns_400_when_index_missing(client, auth_headers, monkeypatch, tmp_path):
    headers = auth_headers(email="api4@example.com")

    monkeypatch.setenv("FAISS_DIR", str(tmp_path / "no_index_here"))
    rag_query.reset_rag_cache()

    payload = {
        "channel": "email",
        "subject": "VPN does not work",
        "body": "Cannot login to VPN",
    }

    r = client.post("/tickets", json=payload, headers=headers)
    assert r.status_code == 200

    ticket_id = r.json()["id"]

    r2 = client.post(f"/tickets/{ticket_id}/answer", headers=headers)
    assert r2.status_code == 400
    assert "Run ingest" in r2.json()["detail"]


def test_answer_works_when_index_exists(client, auth_headers):
    headers = auth_headers(email="api5@example.com")

    payload = {
        "channel": "email",
        "subject": "VPN does not work",
        "body": "Hi, I cannot login to VPN since morning. Please help.",
    }

    r = client.post("/tickets", json=payload, headers=headers)
    assert r.status_code == 200

    ticket_id = r.json()["id"]

    r2 = client.post(f"/tickets/{ticket_id}/answer", headers=headers)
    assert r2.status_code == 200

    data = r2.json()
    assert isinstance(data["suggested_answer"], str)
    assert isinstance(data["sources"], list)



