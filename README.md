# Ticket/Email Copilot (MVP)

An end-to-end backend for handling support tickets (email/web):
- creates and stores tickets
- classifies tickets (category + priority) using an ML baseline (TF-IDF + Logistic Regression)
- records audit logs for traceability (enterprise-style)

## Features (current)
- FastAPI API with Swagger UI (`/docs`)
- SQLite persistence (MVP)
- Classification:
  - ML model if present: `tfidf-logreg-v1`
  - fallback rules if model is not trained: `rules-v0`
- Audit logging: request_id + hashed input + prediction details
- CI: pytest runs on GitHub Actions

## Knowledge Base (RAG)

The project includes a local Retrieval-Augmented Generation (RAG) component
used to suggest answers to tickets based on internal procedures.

- Knowledge base files are stored in `kb/` (PDF / Markdown)
- Documents are embedded using `sentence-transformers`
- Similarity search is performed using a local FAISS index

## RAG Ingest (Required)

Before using the `/answer` endpoint, the knowledge base must be ingested
and indexed locally.

Run once (or whenever KB documents change):

```powershell
python -m app.rag.ingest
```

This will:
- read documents from kb/
- generate mbeddings
- build a FAISS index in faiss_store/
If the index is missing, the /answer endpoint will return HTTP 400
with a message indicating that ingest is required.


## Tech stack
- Python -Requires Python 3.10+ , FastAPI
- SQLAlchemy + SQLite (MVP)
- scikit-learn (TF-IDF + Logistic Regression), joblib
- sentence-transformers, FAISS (local vector search)
- pytest + GitHub Actions (CI)

## Project structure
app/
api/ # routes + schemas
core/ # classifier + utilities
db/ # database + models
ml/ # training + model loading/prediction
data/ # training data (CSV)
models/ # trained model artifact (joblib)
tests/ # pytest tests


## Setup (Windows / PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Initialize DB + run API
powershell
Copy code
python -m app.db.init_db
uvicorn app.main:app --reload
Open:

http://127.0.0.1:8000/docs

## Train ML baseline

Training data:
data/sample_tickets.csv with columns: text,category,priority

Run training:
```powershell
python -m app.ml.train
```

This creates:

models/ticket_clf.joblib
After that, classification endpoint should return:
model_version = tfidf-logreg-v1

## API Endpoints
Create a ticket

POST /tickets

{
  "channel": "email",
  "subject": "VPN does not work",
  "body": "I cannot login to VPN, please help."
}

## Get a ticket
GET /tickets/{ticket_id}

## Classify a ticket

POST /tickets/{ticket_id}/classify
Example response:

{
  "category": "access",
  "priority": 2,
  "confidence": 0.84,
  "model_version": "tfidf-logreg-v1"
}

## Suggest an answer (RAG)

POST /tickets/{ticket_id}/answer

Returns:
- suggested_answer: extracted answer based on internal procedures
- sources: list of document sources and text snippets

This endpoint uses semantic search over the knowledge base (RAG).

## Tests
```powershell
pytest -q
```

