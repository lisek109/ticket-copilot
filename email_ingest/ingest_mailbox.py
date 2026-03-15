import os
import imaplib
import email
from email.header import decode_header
from email.message import Message
from email.utils import parseaddr
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

# Load local environment variables from .env
load_dotenv()

# Base URL of the deployed API
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

# Mailbox configuration
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

# Local files used by the ingestion script
PROCESSED_IDS_FILE = Path("email_ingest/processed_ids.txt")
GENERATED_REPLIES_DIR = Path("email_ingest/generated_replies")


def decode_mime_header(value: Optional[str]) -> str:
    """
    Decode MIME-encoded email headers into readable text.
    """
    if not value:
        return ""

    decoded_parts = decode_header(value)
    result = []

    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(encoding or "utf-8", errors="ignore"))
        else:
            result.append(part)

    return "".join(result)


def extract_text_from_message(msg: Message) -> str:
    """
    Extract plain text body from an email message.
    Priority:
    1. text/plain
    2. fallback to empty string if no plain text body is found
    """
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition") or "")

            # Skip attachments
            if "attachment" in content_disposition.lower():
                continue

            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(
                        part.get_content_charset() or "utf-8",
                        errors="ignore"
                    )
    else:
        if msg.get_content_type() == "text/plain":
            payload = msg.get_payload(decode=True)
            if payload:
                return payload.decode(
                    msg.get_content_charset() or "utf-8",
                    errors="ignore"
                )

    return ""


def extract_sender_name(from_header: str) -> str:
    """
    Extract a readable sender name from the email 'From' header.
    Falls back to an empty string if no usable display name exists.
    """
    display_name, email_address = parseaddr(from_header)
    display_name = decode_mime_header(display_name).strip()

    if display_name:
        # Keep only the first token as a friendly first name
        return display_name.split()[0]

    if email_address:
        return email_address.split("@")[0]

    return ""


def load_processed_ids() -> set[str]:
    """
    Load already processed email Message-IDs from local storage.
    """
    if not PROCESSED_IDS_FILE.exists():
        return set()

    return {
        line.strip()
        for line in PROCESSED_IDS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def save_processed_id(message_id: str) -> None:
    """
    Append a processed Message-ID to local storage.
    """
    PROCESSED_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with PROCESSED_IDS_FILE.open("a", encoding="utf-8") as f:
        f.write(message_id + "\n")


def save_generated_reply(ticket_id: str, sender_name: str, subject: str, reply_text: str) -> None:
    """
    Save the generated reply to a local text file for review.
    This simulates a 'draft' workflow without sending email.
    """
    GENERATED_REPLIES_DIR.mkdir(parents=True, exist_ok=True)

    safe_subject = "".join(c for c in subject if c.isalnum() or c in (" ", "_", "-")).strip()
    safe_subject = safe_subject[:50].replace(" ", "_") or "no_subject"

    output_file = GENERATED_REPLIES_DIR / f"{ticket_id}_{safe_subject}.txt"

    content = (
        f"To: {sender_name or 'Unknown'}\n"
        f"Ticket ID: {ticket_id}\n"
        f"Original Subject: {subject}\n"
        f"{'-' * 80}\n"
        f"{reply_text}\n"
    )

    output_file.write_text(content, encoding="utf-8")


def create_ticket(subject: str, body: str, sender_name: str) -> Optional[str]:
    """
    Create a new ticket via the backend API.
    Sender name is prepended to the body so the LLM can use it in the reply.
    """
    enriched_body = f"Sender name: {sender_name}\n\n{body}" if sender_name else body

    payload = {
        "channel": "email",
        "subject": subject,
        "body": enriched_body,
    }

    response = requests.post(f"{API_BASE}/tickets", json=payload, timeout=30)
    if response.status_code != 200:
        print("Failed to create ticket:", response.text)
        return None

    return response.json()["id"]


def classify_ticket(ticket_id: str) -> dict:
    """
    Run ticket classification and return the API response.
    """
    response = requests.post(f"{API_BASE}/tickets/{ticket_id}/classify", timeout=30)
    response.raise_for_status()
    return response.json()


def answer_ticket(ticket_id: str) -> dict:
    """
    Generate a suggested reply using RAG + LLM.
    """
    response = requests.post(f"{API_BASE}/tickets/{ticket_id}/answer", timeout=60)
    response.raise_for_status()
    return response.json()


def process_unread_emails(limit: int = 3, verbose: bool = True) -> None:
    """
    Connect to the mailbox, fetch a few unread emails, and process them.

    The script:
    - skips emails that were already processed
    - creates tickets through the API
    - runs classification
    - generates suggested replies
    - stores generated replies locally for review
    """
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("Missing EMAIL_ADDRESS or EMAIL_PASSWORD in environment.")
        return

    processed_ids = load_processed_ids()

    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    mail.select("inbox")

    status, messages = mail.search(None, "UNSEEN")
    if status != "OK":
        print("Failed to search mailbox.")
        mail.logout()
        return

    email_ids = messages[0].split()
    if not email_ids:
        print("No unread emails found.")
        mail.logout()
        return

    # Process only the newest emails first
    for email_id in email_ids[-limit:]:
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        if status != "OK":
            print(f"Failed to fetch email ID {email_id.decode()}")
            continue

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        message_id = (msg.get("Message-ID") or "").strip()
        if message_id and message_id in processed_ids:
            if verbose:
                print(f"Skipping already processed email: {message_id}")
            continue

        subject = decode_mime_header(msg.get("Subject"))
        from_header = decode_mime_header(msg.get("From"))
        sender_name = extract_sender_name(from_header)
        body = extract_text_from_message(msg).strip()

        if verbose:
            print("=" * 80)
            print(f"From: {from_header}")
            print(f"Subject: {subject}")

        if not body:
            print("Skipping email: no plain text body found.")
            continue

        # Create ticket in backend
        ticket_id = create_ticket(subject, body, sender_name)
        if not ticket_id:
            continue

        # Run classification (kept for pipeline completeness, but not shown to the end user)
        classification = classify_ticket(ticket_id)

        # Generate AI reply
        answer = answer_ticket(ticket_id)
        suggested_reply = answer["suggested_answer"]

        # Save generated reply locally
        save_generated_reply(ticket_id, sender_name, subject, suggested_reply)

        # Mark message ID as processed
        if message_id:
            save_processed_id(message_id)

        # User-facing output: show only the generated reply
        print("\nGenerated reply:\n")
        print(suggested_reply)
        print("\n" + "-" * 80 + "\n")

        # Optional verbose debug section
        if verbose:
            print("Debug info:")
            print(f"  Ticket ID: {ticket_id}")
            print(f"  Category: {classification['category']}")
            print(f"  Priority: {classification['priority']}")
            print(f"  Answer mode: {answer.get('answer_mode', 'unknown')}")
            print("  Sources:")
            for src in answer["sources"]:
                print(f"    - {src['source']}")

    mail.logout()


if __name__ == "__main__":
    process_unread_emails(limit=1, verbose=True)