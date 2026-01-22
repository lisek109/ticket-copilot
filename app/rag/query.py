from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings

CHROMA_DIR = "chroma_store"

def rag_answer(question: str, k: int = 3) -> dict:
    embeddings = SentenceTransformerEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    store = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
    )

    docs = store.similarity_search(question, k=k)

    # Simple extractive answer for MVP
    context = "\n\n".join(d.page_content for d in docs)
    sources = [
        {
            "source": d.metadata.get("source", "unknown"),
            "snippet": d.page_content[:200],
        }
        for d in docs
    ]

    answer = (
        "Based on internal procedures:\n\n"
        f"{context[:800]}\n\n"
        "Please follow the steps above."
    )

    return {
        "answer": answer,
        "sources": sources,
    }
