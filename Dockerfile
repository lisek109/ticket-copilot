# Use Python 3.10 slim image
FROM python:3.10-slim

# Basic runtime settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FAISS_DIR=faiss_store

WORKDIR /app

# System deps (kept minimal; add more only if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better Docker caching)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code + data + knowledge base
COPY app ./app
COPY data ./data
COPY kb ./kb

# Build artifacts at image build time:
# 1) Train ML model -> models/ticket_clf.joblib
# 2) Build FAISS index -> faiss_store/
RUN python -m app.ml.train && \
    python -m app.rag.ingest

# Expose API port
EXPOSE 8000

# Start command:
# Ensure DB tables exist on container start, then run API
CMD ["sh", "-c", "python -m app.db.init_db && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
