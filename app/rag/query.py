from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
import os

# Directory where FAISS index was saved by ingest.py
FAISS_DIR = os.getenv("FAISS_DIR", "faiss_store")

# Cache objects so we don't reload model/index on every request
_embeddings = None
_store = None

class IndexNotReadyError(RuntimeError):
    """Raised when FAISS index is not available (ingest not run)."""
    pass

def reset_rag_cache():
    """Used by tests to force reloading FAISS index with a different FAISS_DIR."""
    global _embeddings, _store
    _embeddings = None
    _store = None

def _get_store():
    """
    Lazy-load and cache:
    - embedding model
    - FAISS index (from disk)

    This is important for performance and stability in FastAPI.
    """
    global _embeddings, _store

    if _embeddings is None:
        _embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    if _store is None:
        try:
            # Loads FAISS index + docstore from disk
            # allow_dangerous_deserialization=True is needed because LangChain stores metadata via pickle
            _store = FAISS.load_local(
                FAISS_DIR,
                embeddings=_embeddings,
                allow_dangerous_deserialization=True,
            )
        except Exception as e:
            # Make API return a clean 400 instead of 500
            raise IndexNotReadyError(
                f"FAISS index not found or cannot be loaded from '{FAISS_DIR}'. Run ingest first."
            ) from e

    return _store


def rag_answer(question: str, k: int = 3) -> dict:
    """
    Retrieve top-k relevant KB chunks using FAISS similarity search
    and return a simple extractive answer + sources.
    """
    store = _get_store()

    # Similarity search returns k most similar chunks
    docs = store.similarity_search(question, k=k)

    # Join retrieved chunks into a single context
    context = "\n\n".join(d.page_content for d in docs)

    # Minimal citations: where chunk came from + snippet
    sources = [
        {
            "source": d.metadata.get("source", "unknown"),
            "snippet": d.page_content[:200],
        }
        for d in docs
    ]

    # MVP answer: just show extracted context (no LLM)
    answer = (
        "Based on internal procedures:\n\n"
        f"{context[:800]}\n\n"
        "Please follow the steps above."
    )

    return {
        "answer": answer,
        "sources": sources,
    }
