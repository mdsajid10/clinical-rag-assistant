"""
Data ingestion script.
Loads PDFs from data/, splits them into chunks, embeds them,
upserts into Pinecone with source metadata, and copies PDFs
to static/pdfs/ for serving via the web UI.
"""

import os
import sys
import shutil

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from services.pinecone_service import upsert_documents

# Where PDFs are served for clickable links
STATIC_PDF_DIR = os.path.join(os.path.dirname(__file__), "static", "pdfs")


def load_documents(data_dir: str) -> list:
    """Load all PDF files from *data_dir*."""
    loader = DirectoryLoader(
        data_dir,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=True,
    )
    docs = loader.load()
    print(f"[ingest] Loaded {len(docs)} pages from PDFs.")
    return docs


def load_single_pdf(filepath: str) -> list:
    """Load a single PDF file."""
    loader = PyPDFLoader(filepath)
    docs = loader.load()
    print(f"[ingest] Loaded {len(docs)} pages from {os.path.basename(filepath)}.")
    return docs


def split_documents(docs: list) -> list:
    """Split documents using RecursiveCharacterTextSplitter."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    # Enrich metadata for every chunk
    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        chunk.metadata["source_document"] = os.path.basename(source)
        chunk.metadata["page_number"] = chunk.metadata.get("page", 0) + 1
    print(f"[ingest] Created {len(chunks)} chunks.")
    return chunks


def copy_pdfs_to_static(data_dir: str) -> None:
    """Copy all PDFs from data/ to static/pdfs/ for web serving."""
    os.makedirs(STATIC_PDF_DIR, exist_ok=True)
    for fname in os.listdir(data_dir):
        if fname.lower().endswith(".pdf"):
            src = os.path.join(data_dir, fname)
            dst = os.path.join(STATIC_PDF_DIR, fname)
            shutil.copy2(src, dst)
    print(f"[ingest] Copied PDFs to {STATIC_PDF_DIR}")


def ingest_single_file(filepath: str) -> dict:
    """
    Ingest a single PDF file: load → split → embed → upsert.
    Also copies the PDF to static/pdfs/ for serving.
    Returns a summary dict.
    """
    docs = load_single_pdf(filepath)
    if not docs:
        return {"status": "error", "message": "No pages found in PDF."}

    chunks = split_documents(docs)
    upsert_documents(chunks)

    # Copy to static folder
    os.makedirs(STATIC_PDF_DIR, exist_ok=True)
    dst = os.path.join(STATIC_PDF_DIR, os.path.basename(filepath))
    shutil.copy2(filepath, dst)

    return {
        "status": "ok",
        "filename": os.path.basename(filepath),
        "pages": len(docs),
        "chunks": len(chunks),
    }


def run_ingestion() -> None:
    """Full ingestion pipeline: load → split → embed → upsert."""
    if not os.path.isdir(DATA_DIR):
        print(f"[ingest] Data directory not found: {DATA_DIR}")
        sys.exit(1)

    docs = load_documents(DATA_DIR)
    if not docs:
        print("[ingest] No PDF documents found. Add PDFs to data/ and retry.")
        sys.exit(1)

    chunks = split_documents(docs)
    print("[ingest] Uploading to Pinecone …")
    upsert_documents(chunks)

    # Copy PDFs for clickable links
    copy_pdfs_to_static(DATA_DIR)

    print("[ingest] Ingestion complete ✓")


if __name__ == "__main__":
    run_ingestion()
