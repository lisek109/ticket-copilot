from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma

# Path to knowledge base documents (PDF / Markdown / TXT)
KB_PATH = Path("kb")

# Directory where Chroma will persist vector embeddings
CHROMA_DIR = Path("chroma_store")

def load_documents():
    """
    Load all documents from KB directory into LangChain Document objects.
    Supports PDF and text-based files.
    """
    docs = []

    for path in KB_PATH.glob("*"):
        if path.suffix.lower() == ".pdf":
            # Load PDF pages as separate documents
            docs.extend(PyPDFLoader(str(path)).load())

        elif path.suffix.lower() in {".md", ".txt"}:
            # Load Markdown / text files
            docs.extend(TextLoader(str(path), encoding="utf-8").load())

    return docs

def ingest():
    """
    Ingest KB documents into Chroma:
    - load documents
    - split into overlapping text chunks
    - compute embeddings
    - persist vectors on disk
    """
    documents = load_documents()

    # Split documents into smaller overlapping chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,      # max characters per chunk
        chunk_overlap=150,   # overlap to preserve context
    )
    chunks = splitter.split_documents(documents)

    # SentenceTransformer model used to compute text embeddings
    embeddings = SentenceTransformerEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    # Create / overwrite Chroma vector store on disk
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    print(f"Ingested {len(chunks)} chunks into Chroma")

if __name__ == "__main__":
    # Run ingestion as a standalone script
    ingest()
