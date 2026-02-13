# Ticket/Email Copilot (MVP)

An end-to-end backend for handling support tickets (email/web):
- creates and stores tickets
- classifies tickets (category + priority) using an ML baseline (TF-IDF + Logistic Regression)
- records audit logs for traceability (enterprise-style)

## Architecture Overview

                          ┌──────────────────────────────┐
                          │        GitHub Actions         │
                          │  (CI + CD Pipeline on push)   │
                          └──────────────┬───────────────┘
                                         │
                                         │ build + push image
                                         ▼
                         ┌────────────────────────────────────┐
                         │      Azure Container Registry       │
                         │   ticketcopilotprojectacr.azurecr.io│
                         └──────────────────┬──────────────────┘
                                            │
                                            │ container_image tag (commit SHA)
                                            ▼
                    ┌──────────────────────────────────────────────────┐
                    │              Terraform (IaC)                      │
                    │  - Container Apps Environment                     │
                    │  - Container App (FastAPI API)                    │
                    │  - Log Analytics Workspace                        │
                    │  - Budget + Alerts                                │
                    └──────────────────┬───────────────────────────────┘
                                       │ terraform apply
                                       ▼
                     ┌────────────────────────────────────────────┐
                     │         Azure Container Apps (API)          │
                     │  - Runs Docker image                        │
                     │  - Autoscaling (incl. scale-to-zero)        │
                     │  - Public HTTPS endpoint                    │
                     └──────────────────┬──────────────────────────┘
                                        │
                                        │ HTTP requests
                                        ▼
                         ┌──────────────────────────────────┐
                         │            FastAPI API            │
                         │  - Ticket creation                │
                         │  - Classification (ML)            │
                         │  - RAG answer suggestions         │
                         │  - Audit logging                  │
                         └──────────────────┬────────────────┘
                                            │
                                            │ local storage inside container
                                            ▼
                   ┌────────────────────────────────────────────────────┐
                   │                     Application                     │
                   │                                                    │
                   │  SQLite DB:                                        │
                   │   - tickets                                        │
                   │   - audit logs                                     │
                   │                                                    │
                   │  ML model (joblib):                                │
                   │   - TF-IDF + Logistic Regression                   │
                   │                                                    │
                   │  RAG subsystem:                                    │
                   │   - kb/ documents                                  │
                   │   - FAISS index (faiss_store/)                     │
                   └────────────────────────────────────────────────────┘


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

## LLM Answer Synthesis (Azure OpenAI)

The `/answer` endpoint supports LLM-based response drafting:
- retrieves relevant procedure snippets (FAISS RAG)
- synthesizes a concise reply using Azure OpenAI
- returns citations to the internal KB sources

If Azure OpenAI is not configured, the system falls back to an extractive answer.



## Tech stack
- Python -Requires Python 3.10+ , FastAPI
- SQLAlchemy + SQLite (MVP)
- scikit-learn (TF-IDF + Logistic Regression), joblib
- sentence-transformers, FAISS (local vector search)
- pytest + GitHub Actions (CI)
- Docker & docker-compose
- Terraform (Azure Container Apps)

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

## Run with Docker

The project can be run in a fully containerized setup.
The Docker image builds all required artifacts at build time:
- ML classification model
- FAISS vector index for the knowledge base

### Build and run
```bash
docker compose up --build

Access

API docs: http://localhost:8000/docs

After startup:

/tickets/{id}/classify uses the trained ML model

/tickets/{id}/answer works immediately (FAISS index is prebuilt in the image)
```


## Infrastructure (Terraform + Azure)

The project includes Infrastructure as Code (IaC) definitions
for deploying the API to Azure using **Terraform** and **Azure Container Apps**.

### Provisioned resources
- Resource Group
- Azure Container Registry (ACR)
- Azure Container Apps Environment
- Container App (FastAPI API)
- Log Analytics Workspace
- Monthly cost budget with email alerts

### Why Azure Container Apps?
- Docker-first deployment model
- No Kubernetes management overhead
- Autoscaling (including scale-to-zero)
- Well suited for small/medium backend + AI services

### Deployment flow (manual)
1. Build Docker image locally
2. Provision Azure infrastructure with Terraform
3. Push Docker image to Azure Container Registry
4. Deploy image via Azure Container Apps

> Terraform state is stored locally for demo purposes.
> The setup is intentionally simplified (single environment, admin ACR access)
> to keep the project focused on backend + ML/RAG logic.

### Pushing image to Azure Container Registry (example)

After provisioning infrastructure, the Docker image can be pushed to ACR:

```bash
az acr login --name <acrName>

docker tag ticket-email-copilot-api:latest \
  <loginServer>/ticket-email-copilot-api:latest

docker push <loginServer>/ticket-email-copilot-api:latest
```
Then set container_image in terraform.tfvars and re-apply Terraform.

## Continuous Deployment (CD)

The project includes a GitHub Actions CD pipeline.

On every push to `main`:
- A Docker image is built and tagged with the commit SHA
- The image is pushed to Azure Container Registry (ACR)
- Terraform applies infrastructure changes and updates the Container App

This ensures reproducible and automated deployments to Azure Container Apps.
