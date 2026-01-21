from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from app.ml.model import build_pipeline, save_model

DATA_PATH = "data/sample_tickets.csv"

def main() -> None:
    df = pd.read_csv(DATA_PATH)
    X = df["text"].astype(str)
    y = df["category"].astype(str)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y if y.nunique() > 1 else None
    )

    model = build_pipeline()
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print(classification_report(y_test, preds))

    save_model(model)
    print("Saved model to models/ticket_clf.joblib")

if __name__ == "__main__":
    main()
