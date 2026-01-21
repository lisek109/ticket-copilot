from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import classification_report, f1_score

from app.ml.model import build_pipeline, save_model

DATA_PATH = "data/sample_tickets.csv"
REPORTS_DIR = Path("reports")
METRICS_PATH = REPORTS_DIR / "metrics.json"

def main() -> None:
    df = pd.read_csv(DATA_PATH)

    X = df["text"].astype(str)
    y = df["category"].astype(str)

    model = build_pipeline()

    # Cross-validation gives a more stable signal on small datasets
    n_splits = 5 if len(df) >= 40 else 3
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    y_pred = cross_val_predict(model, X, y, cv=cv)   
    report = classification_report(y, y_pred, output_dict=True, zero_division=0)

    macro_f1 = f1_score(y, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y, y_pred, average="weighted", zero_division=0)

    print("Cross-validation report (aggregated over folds):")
    print(classification_report(y, y_pred, zero_division=0))
    print(f"macro_f1={macro_f1:.3f} weighted_f1={weighted_f1:.3f}")

    # Train final model on full data and save artifact for API
    model.fit(X, y)
    save_model(model)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "n_samples": int(len(df)),
        "n_splits": int(n_splits),
        "macro_f1": float(macro_f1),
        "weighted_f1": float(weighted_f1),
        "report": report,
    }
    METRICS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved metrics to {METRICS_PATH}")
    print("Saved model to models/ticket_clf.joblib")

if __name__ == "__main__":
    main()
