from dataclasses import dataclass
from app.ml.model import load_model, predict, priority_from_category, MODEL_VERSION

@dataclass
class ClassificationResult:
    category: str
    priority: int
    confidence: float
    model_version: str

_model = None

def _get_model():
    global _model
    if _model is None:
        _model = load_model()
    return _model

def classify_ticket(subject: str, body: str) -> ClassificationResult:
    text = f"{subject} {body}".strip()

    model = _get_model()
    if model is not None:
        cat, conf = predict(model, text)
        prio = priority_from_category(cat)
        return ClassificationResult(cat, prio, conf, MODEL_VERSION)

    # Fallback 
    lower = text.lower()
    if any(k in lower for k in ["vpn", "login", "password", "account locked"]):
        return ClassificationResult("access", 2, 0.62, "rules-v0")
    if any(k in lower for k in ["outage", "down", "critical", "cannot access"]):
        return ClassificationResult("incident", 1, 0.66, "rules-v0")
    if any(k in lower for k in ["invoice", "billing", "payment"]):
        return ClassificationResult("billing", 3, 0.60, "rules-v0")
    return ClassificationResult("general", 4, 0.55, "rules-v0")
