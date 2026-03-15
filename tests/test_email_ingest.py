from pathlib import Path

from email_ingest.ingest_mailbox import (
    decode_mime_header,
    extract_sender_name,
    load_processed_ids,
    save_processed_id,
    save_generated_reply,
)


def test_decode_mime_header_returns_plain_text():
    value = "Test subject"
    assert decode_mime_header(value) == "Test subject"


def test_extract_sender_name_from_display_name():
    sender = "Thomas Tunheim <thomas@example.com>"
    assert extract_sender_name(sender) == "Thomas"


def test_extract_sender_name_from_email_only():
    sender = "noreply@example.com"
    assert extract_sender_name(sender) == "noreply"


def test_save_and_load_processed_ids(tmp_path, monkeypatch):
    processed_file = tmp_path / "processed_ids.txt"

    # Redirect processed IDs file to a temporary location
    monkeypatch.setattr("email_ingest.ingest_mailbox.PROCESSED_IDS_FILE", processed_file)

    save_processed_id("<msg-123@example.com>")
    save_processed_id("<msg-456@example.com>")

    processed = load_processed_ids()

    assert "<msg-123@example.com>" in processed
    assert "<msg-456@example.com>" in processed
    assert len(processed) == 2


def test_save_generated_reply_creates_file(tmp_path, monkeypatch):
    replies_dir = tmp_path / "generated_replies"

    # Redirect generated replies directory to a temporary location
    monkeypatch.setattr("email_ingest.ingest_mailbox.GENERATED_REPLIES_DIR", replies_dir)

    save_generated_reply(
        ticket_id="ticket-001",
        sender_name="Thomas",
        subject="VPN issue",
        reply_text="Hello Thomas,\n\nPlease try again.",
    )

    files = list(replies_dir.glob("*.txt"))

    assert len(files) == 1

    content = files[0].read_text(encoding="utf-8")
    assert "Thomas" in content
    assert "VPN issue" in content
    assert "Please try again." in content