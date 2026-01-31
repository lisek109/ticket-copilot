# ==========================
# Stage 1: builder
# ==========================
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FAISS_DIR=faiss_store

WORKDIR /app

# Build deps only here
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps (runtime)
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt 
 


# Copy only what we need to build artifacts
COPY app ./app
COPY data ./data
COPY kb ./kb

# Build artifacts (model + FAISS index)
RUN python -m app.ml.train && \
    python -m app.rag.ingest && \
    rm -rf /root/.cache/pip /root/.cache/huggingface

# ==========================
# Stage 2: runtime
# ==========================
FROM python:3.10-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FAISS_DIR=faiss_store

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /usr/local /usr/local

# Copy app + built artifacts
COPY --from=builder /app /app

EXPOSE 8000

CMD ["sh", "-c", "python -m app.db.init_db && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
