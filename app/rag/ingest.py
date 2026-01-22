from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS

# Folder with your knowledge base files (pdf/md/txt)
KB_PATH = Path("kb")

# Directory where FAISS index + metadata will be saved
FAISS_DIR = Path("faiss_store")


def load_documents():
    """Load all KB files into LangChain Document objects."""
    docs = []
    for path in KB_PATH.glob("*"):
        if path.suffix.lower() == ".pdf":
            # Each PDF page becomes a separate Document
            docs.extend(PyPDFLoader(str(path)).load())
        elif path.suffix.lower() in {".md", ".txt"}:
            # One file -> one Document (then  split)
            docs.extend(TextLoader(str(path), encoding="utf-8").load())
    return docs


def ingest():
    """
    Offline ingestion step:
    - load KB documents
    - split into chunks
    - compute embeddings
    - build FAISS index
    - save index to disk (faiss_store/)
    """
    documents = load_documents()

    # Split text into overlapping chunks to preserve context
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
    )
    chunks = splitter.split_documents(documents)

    # Local embedding model (runs on mymachine; uses PyTorch)
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    # Build FAISS vector index from documents + embeddings
    store = FAISS.from_documents(chunks, embedding=embeddings)

    # Persist index to disk
    FAISS_DIR.mkdir(parents=True, exist_ok=True)
    store.save_local(str(FAISS_DIR))

    print(f"Ingested {len(chunks)} chunks into FAISS at {FAISS_DIR}")


if __name__ == "__main__":
    ingest()
