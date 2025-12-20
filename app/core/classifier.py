from dataclasses import dataclass

@dataclass
class ClassificationResult:
    category: str
    priority: int
    confidence: float
    model_version: str

def classify_ticket(subject: str, body: str) -> ClassificationResult:
    """
    MVP classifier: simple keyword-based rules.
    """
    text = f"{subject} {body}".lower()

    if any(k in text for k in ["vpn", "login", "password", "account locked"]):
        return ClassificationResult("access", 2, 0.62, "rules-v0")

    if any(k in text for k in ["outage", "down", "critical", "cannot access"]):
        return ClassificationResult("incident", 1, 0.66, "rules-v0")

    if any(k in text for k in ["invoice", "billing", "payment"]):
        return ClassificationResult("billing", 3, 0.60, "rules-v0")

    return ClassificationResult("general", 4, 0.55, "rules-v0")
