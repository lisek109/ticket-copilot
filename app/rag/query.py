from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings

# Directory where Chroma vector store is persisted on disk
CHROMA_DIR = "chroma_store"

# Module-level cache (initialized once per process)
_embeddings = None
_store = None

def _get_store():
    """
    Lazily initialize and cache:
    - embedding model (SentenceTransformer)
    - Chroma vector store

    This avoids re-loading PyTorch / models on every request,
    which is expensive and can cause DLL issues on Windows.
    """
    global _embeddings, _store

    if _store is None:
        # Load embedding model (uses PyTorch under the hood)
        _embeddings = SentenceTransformerEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )

        # Connect to existing Chroma store on disk
        _store = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=_embeddings,
        )

    return _store

def rag_answer(question: str, k: int = 3) -> dict:
    """
    Retrieve top-k most relevant knowledge base fragments
    and build a simple extractive answer.

    Args:
        question: user question / ticket text
        k: number of KB chunks to retrieve

    Returns:
        dict with:
        - answer: text response based on KB
        - sources: list of source documents/snippets
    """
    store = _get_store()

    # Vector similarity search against KB embeddings
    docs = store.similarity_search(question, k=k)

    # Concatenate retrieved chunks into a single context
    context = "\n\n".join(d.page_content for d in docs)

    # Collect traceability information (citations)
    sources = [
        {
            "source": d.metadata.get("source", "unknown"),
            "snippet": d.page_content[:200],
        }
        for d in docs
    ]

    # Simple MVP answer (no LLM yet)
    answer = (
        "Based on internal procedures:\n\n"
        f"{context[:800]}\n\n"
        "Please follow the steps above."
    )

    return {
        "answer": answer,
        "sources": sources,
    }
