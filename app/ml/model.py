from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import joblib

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

MODEL_DIR = Path("models")
MODEL_PATH = MODEL_DIR / "ticket_clf.joblib"
MODEL_VERSION = "tfidf-logreg-v1"

@dataclass
class MLResult:
    category: str
    priority: int
    confidence: float
    model_version: str = MODEL_VERSION

def build_pipeline() -> Pipeline:
    # Simple, strong baseline for text classification
    return Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ("clf", LogisticRegression(max_iter=1000)),
        ]
    )

def save_model(model: Pipeline) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

def load_model() -> Pipeline | None:
    if MODEL_PATH.exists():
        return joblib.load(MODEL_PATH)
    return None

def predict(model: Pipeline, text: str) -> tuple[str, float]:
    # Returns (label, confidence)
    proba = model.predict_proba([text])[0]
    idx = int(proba.argmax())
    label = model.classes_[idx]
    conf = float(proba[idx])
    return str(label), conf

def priority_from_category(category: str) -> int:
    # Simple mapping 
    mapping = {
        "incident": 1,
        "access": 2,
        "billing": 3,
        "general": 4,
    }
    return int(mapping.get(category, 4))
