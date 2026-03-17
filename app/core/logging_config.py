import logging


def mask_email(email: str) -> str:
    """
    Obfuscate an email address for safer logging.
    Example:
    thomas@example.com -> th****@example.com
    """
    if not email or "@" not in email:
        return email

    local_part, domain = email.split("@", 1)

    if len(local_part) <= 2:
        masked_local = "*" * len(local_part)
    else:
        masked_local = local_part[:2] + "*" * (len(local_part) - 2)

    return f"{masked_local}@{domain}"


def configure_logging() -> None:
    """
    Configure application-wide logging.
    Logs are sent to stdout, which works well both locally and in Azure.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )