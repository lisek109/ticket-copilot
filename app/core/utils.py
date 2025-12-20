import hashlib

def sha256_text(text: str) -> str:
    """Hash text so we can log traceability without storing raw sensitive content."""
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
