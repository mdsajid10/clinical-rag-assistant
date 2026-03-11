"""
Retriever module – performs semantic search against Pinecone and
formats results with source citations.
"""

from __future__ import annotations

from dataclasses import dataclass
from services.pinecone_service import get_vectorstore
from config import TOP_K


@dataclass
class RetrievedChunk:
    """A single retrieved document chunk with citation info."""
    content: str
    source_document: str
    page_number: int
    score: float | None = None


def retrieve(query: str, k: int = TOP_K) -> list[RetrievedChunk]:
    """
    Convert *query* to an embedding, search Pinecone,
    and return the top-k chunks with metadata.
    """
    vs = get_vectorstore()
    results = vs.similarity_search_with_score(query, k=k)

    chunks: list[RetrievedChunk] = []
    for doc, score in results:
        chunks.append(
            RetrievedChunk(
                content=doc.page_content,
                source_document=doc.metadata.get("source_document", "unknown"),
                page_number=int(doc.metadata.get("page_number", 0)),
                score=score,
            )
        )
    return chunks


def format_context(chunks: list[RetrievedChunk]) -> str:
    """Build a context string from retrieved chunks for the LLM prompt."""
    parts: list[str] = []
    for i, c in enumerate(chunks, 1):
        parts.append(
            f"[Source {i}: {c.source_document}, Page {c.page_number}]\n"
            f"{c.content}"
        )
    return "\n\n---\n\n".join(parts)


def format_sources(chunks: list[RetrievedChunk]) -> list[dict]:
    """Return a JSON-serialisable list of source citations."""
    seen: set[tuple[str, int]] = set()
    sources: list[dict] = []
    for c in chunks:
        key = (c.source_document, c.page_number)
        if key not in seen:
            seen.add(key)
            sources.append(
                {"document": c.source_document, "page": c.page_number}
            )
    return sources
