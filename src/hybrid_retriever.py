"""
Hybrid retriever – combines Pinecone vector search with BM25 keyword
search using Reciprocal Rank Fusion (RRF) for improved retrieval.
"""

from __future__ import annotations

from rank_bm25 import BM25Okapi

from src.retriever import RetrievedChunk, retrieve as vector_retrieve
from services.pinecone_service import get_vectorstore
from config import TOP_K


# ── BM25 corpus (lazy-loaded) ───────────────────────────────────────────

_bm25: BM25Okapi | None = None
_corpus_docs: list[dict] | None = None  # [{content, source_document, page_number}]


def _build_bm25_index() -> None:
    """Build BM25 index from all documents currently in Pinecone."""
    global _bm25, _corpus_docs

    vs = get_vectorstore()
    # Fetch a large set of docs for BM25 corpus
    # We use a broad query to pull representative docs
    all_docs = vs.similarity_search("medical clinical health disease treatment", k=200)

    _corpus_docs = []
    tokenized: list[list[str]] = []

    for doc in all_docs:
        entry = {
            "content": doc.page_content,
            "source_document": doc.metadata.get("source_document", "unknown"),
            "page_number": int(doc.metadata.get("page_number", 0)),
        }
        _corpus_docs.append(entry)
        tokenized.append(doc.page_content.lower().split())

    if tokenized:
        _bm25 = BM25Okapi(tokenized)


def _bm25_search(query: str, k: int = TOP_K) -> list[RetrievedChunk]:
    """Keyword search using BM25."""
    global _bm25, _corpus_docs

    if _bm25 is None or _corpus_docs is None:
        _build_bm25_index()

    if _bm25 is None or not _corpus_docs:
        return []

    tokenized_query = query.lower().split()
    scores = _bm25.get_scores(tokenized_query)

    # Get top-k indices
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:k]

    chunks: list[RetrievedChunk] = []
    for idx, score in ranked:
        if score > 0:
            doc = _corpus_docs[idx]
            chunks.append(
                RetrievedChunk(
                    content=doc["content"],
                    source_document=doc["source_document"],
                    page_number=doc["page_number"],
                    score=float(score),
                )
            )
    return chunks


def _reciprocal_rank_fusion(
    results_lists: list[list[RetrievedChunk]],
    k: int = 60,
) -> list[RetrievedChunk]:
    """
    Merge multiple ranked lists using Reciprocal Rank Fusion.
    RRF score = sum(1 / (k + rank)) across all lists.
    """
    scores: dict[str, float] = {}
    chunk_map: dict[str, RetrievedChunk] = {}

    for results in results_lists:
        for rank, chunk in enumerate(results):
            key = f"{chunk.source_document}:{chunk.page_number}:{chunk.content[:80]}"
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            if key not in chunk_map:
                chunk_map[key] = chunk

    sorted_keys = sorted(scores, key=scores.get, reverse=True)
    return [chunk_map[k] for k in sorted_keys]


def hybrid_retrieve(query: str, k: int = TOP_K) -> list[RetrievedChunk]:
    """
    Perform hybrid retrieval: vector search + BM25 keyword search,
    merged with Reciprocal Rank Fusion, returning top-k results.
    """
    # 1. Vector (semantic) search
    vector_results = vector_retrieve(query, k=k)

    # 2. BM25 (keyword) search
    bm25_results = _bm25_search(query, k=k)

    # 3. Merge with RRF
    fused = _reciprocal_rank_fusion([vector_results, bm25_results])

    return fused[:k]


def rebuild_bm25_index() -> None:
    """Force rebuild of the BM25 index (e.g. after new document upload)."""
    global _bm25, _corpus_docs
    _bm25 = None
    _corpus_docs = None
    _build_bm25_index()
