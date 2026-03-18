from unittest.mock import Mock, patch

from email_ingest.ingest_mailbox import (
    login_and_get_token,
    create_ticket,
    classify_ticket,
    answer_ticket,
)


@patch("email_ingest.ingest_mailbox.requests.post")
def test_login_and_get_token_success(mock_post, monkeypatch):
    monkeypatch.setattr("email_ingest.ingest_mailbox.AUTH_EMAIL", "supportbot@example.com")
    monkeypatch.setattr("email_ingest.ingest_mailbox.AUTH_PASSWORD", "StrongPassword123")

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "test-token"}
    mock_post.return_value = mock_response

    token = login_and_get_token()

    assert token == "test-token"


@patch("email_ingest.ingest_mailbox.requests.post")
def test_login_and_get_token_returns_none_on_failure(mock_post, monkeypatch):
    monkeypatch.setattr("email_ingest.ingest_mailbox.AUTH_EMAIL", "supportbot@example.com")
    monkeypatch.setattr("email_ingest.ingest_mailbox.AUTH_PASSWORD", "WrongPassword")

    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_post.return_value = mock_response

    token = login_and_get_token()

    assert token is None


@patch("email_ingest.ingest_mailbox.requests.post")
def test_create_ticket_uses_bearer_token(mock_post):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "ticket-123"}
    mock_post.return_value = mock_response

    ticket_id = create_ticket(
        subject="VPN issue",
        body="Cannot login to VPN",
        sender_name="Thomas",
        token="jwt-token",
    )

    assert ticket_id == "ticket-123"

    _, kwargs = mock_post.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer jwt-token"
    assert kwargs["json"]["channel"] == "email"
    assert "Sender name: Thomas" in kwargs["json"]["body"]


@patch("email_ingest.ingest_mailbox.requests.post")
def test_classify_ticket_uses_bearer_token(mock_post):
    mock_response = Mock()
    mock_response.json.return_value = {
        "category": "access",
        "priority": 2,
        "confidence": 0.9,
        "model_version": "tfidf-logreg-v1",
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = classify_ticket("ticket-123", "jwt-token")

    assert result["category"] == "access"

    _, kwargs = mock_post.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer jwt-token"


@patch("email_ingest.ingest_mailbox.requests.post")
def test_answer_ticket_uses_bearer_token(mock_post):
    mock_response = Mock()
    mock_response.json.return_value = {
        "suggested_answer": "Hello Thomas, please try again.",
        "sources": [],
        "answer_mode": "llm",
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = answer_ticket("ticket-123", "jwt-token")

    assert result["answer_mode"] == "llm"

    _, kwargs = mock_post.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer jwt-token"