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

import logging

# Load local environment variables from .env
load_dotenv()

logger = logging.getLogger(__name__)

# Base URL of the deployed API
#API_BASE = os.getenv("API_BASE", "http://localhost:8000")
API_BASE = "http://localhost:8000"

# Mailbox configuration
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

# API authentication for ingestion service user
AUTH_EMAIL = os.getenv("AUTH_EMAIL", "")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "")

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

            # Ignore attachments
            if "attachment" in content_disposition.lower():
                continue

            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(
                        part.get_content_charset() or "utf-8",
                        errors="ignore",
                    )
    else:
        if msg.get_content_type() == "text/plain":
            payload = msg.get_payload(decode=True)
            if payload:
                return payload.decode(
                    msg.get_content_charset() or "utf-8",
                    errors="ignore",
                )

    return ""


def extract_sender_name(from_header: str) -> str:
    """
    Extract a readable sender name from the email 'From' header.
    """
    display_name, email_address = parseaddr(from_header)
    display_name = decode_mime_header(display_name).strip()

    if display_name:
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

    with PROCESSED_IDS_FILE.open("a", encoding="utf-8") as file:
        file.write(message_id + "\n")


def save_generated_reply(ticket_id: str, sender_name: str, subject: str, reply_text: str) -> None:
    """
    Save the generated reply to a local text file for review.
    This simulates a draft workflow without sending email.
    """
    GENERATED_REPLIES_DIR.mkdir(parents=True, exist_ok=True)

    safe_subject = "".join(
        char for char in subject if char.isalnum() or char in (" ", "_", "-")
    ).strip()
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
    logger.info("Saved generated reply draft", extra={"ticket_id": ticket_id, "file": str(output_file)})


def login_and_get_token() -> Optional[str]:
    """
    Authenticate against the API and return a JWT access token.
    """
    if not AUTH_EMAIL or not AUTH_PASSWORD:
        logger.error("Missing AUTH_EMAIL or AUTH_PASSWORD in environment")
        return None

    payload = {
        "email": AUTH_EMAIL,
        "password": AUTH_PASSWORD,
    }

    try:
        response = requests.post(f"{API_BASE}/auth/login", json=payload, timeout=30)
    except requests.RequestException as exc:
        logger.exception("Failed to connect to auth endpoint", exc_info=exc)
        return None

    if response.status_code != 200:
        logger.error("Failed to login to API", extra={"status_code": response.status_code, "response": response.text})
        return None

    token = response.json()["access_token"]
    logger.info("Successfully authenticated ingestion service user", extra={"auth_email": AUTH_EMAIL})
    return token


def create_ticket(subject: str, body: str, sender_name: str, token: str) -> Optional[str]:
    """
    Create a new ticket via the backend API.

    Sender name is prepended to the body so the LLM can use it
    when drafting a reply.
    """
    enriched_body = f"Sender name: {sender_name}\n\n{body}" if sender_name else body

    payload = {
        "channel": "email",
        "subject": subject,
        "body": enriched_body,
    }

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.post(
            f"{API_BASE}/tickets",
            json=payload,
            headers=headers,
            timeout=30,
        )
    except requests.RequestException as exc:
        logger.exception("Failed to create ticket", exc_info=exc)
        return None

    if response.status_code != 200:
        logger.error("Ticket creation failed", extra={"status_code": response.status_code, "response": response.text})
        return None

    ticket_id = response.json()["id"]
    logger.info("Created ticket from email", extra={"ticket_id": ticket_id, "subject": subject})
    return ticket_id


def classify_ticket(ticket_id: str, token: str) -> dict:
    """
    Run ticket classification and return the API response.
    """
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.post(
        f"{API_BASE}/tickets/{ticket_id}/classify",
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def answer_ticket(ticket_id: str, token: str) -> dict:
    """
    Generate a suggested reply using RAG + LLM.
    """
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.post(
        f"{API_BASE}/tickets/{ticket_id}/answer",
        headers=headers,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def process_unread_emails(limit: int = 1, verbose: bool = True) -> None:
    """
    Connect to the mailbox, fetch a few unread emails, and process them.

    The script:
    - skips emails that were already processed
    - creates tickets through the API using JWT auth
    - runs classification
    - generates suggested replies
    - stores generated replies locally for review
    """
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        logger.error("Missing EMAIL_ADDRESS or EMAIL_PASSWORD in environment")
        return

    token = login_and_get_token()
    if not token:
        logger.error("Cannot continue without API token")
        return

    processed_ids = load_processed_ids()

    logger.info("Connecting to mailbox", extra={"imap_host": IMAP_HOST, "email_address": EMAIL_ADDRESS})

    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    mail.select("inbox")

    status, messages = mail.search(None, "UNSEEN")
    if status != "OK":
        logger.error("Failed to search mailbox")
        mail.logout()
        return

    email_ids = messages[0].split()
    if not email_ids:
        logger.info("No unread emails found")
        mail.logout()
        return

    logger.info("Unread emails found", extra={"count": len(email_ids)})

    # Process only the newest few emails
    for email_id in email_ids[-limit:]:
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        if status != "OK":
            logger.warning("Failed to fetch email", extra={"email_id": email_id.decode(errors='ignore')})
            continue

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        message_id = (msg.get("Message-ID") or "").strip()
        if message_id and message_id in processed_ids:
            logger.info("Skipping already processed email", extra={"message_id": message_id})
            continue

        subject = decode_mime_header(msg.get("Subject"))
        from_header = decode_mime_header(msg.get("From"))
        sender_name = extract_sender_name(from_header)
        body = extract_text_from_message(msg).strip()

        if verbose:
            print("=" * 80)
            print(f"From: {from_header}")
            print(f"Subject: {subject}")

        logger.info(
            "Processing unread email",
            extra={
                "message_id": message_id,
                "subject": subject,
                "sender_name": sender_name,
            },
        )

        if not body:
            logger.warning("Skipping email without plain text body", extra={"subject": subject})
            continue

        ticket_id = create_ticket(subject, body, sender_name, token)
        if not ticket_id:
            continue

        classification = classify_ticket(ticket_id, token)
        answer = answer_ticket(ticket_id, token)
        suggested_reply = answer["suggested_answer"]

        save_generated_reply(ticket_id, sender_name, subject, suggested_reply)

        if message_id:
            save_processed_id(message_id)

        # User-facing output: show only the generated reply
        print("\nGenerated reply:\n")
        print(suggested_reply)
        print("\n" + "-" * 80 + "\n")

        logger.info(
            "Email processed successfully",
            extra={
                "ticket_id": ticket_id,
                "category": classification.get("category"),
                "priority": classification.get("priority"),
                "answer_mode": answer.get("answer_mode"),
            },
        )

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
    logger.info("Mailbox processing finished")


if __name__ == "__main__":
    process_unread_emails(limit=3, verbose=True)