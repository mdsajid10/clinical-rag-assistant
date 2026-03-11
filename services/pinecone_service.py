"""
Pinecone service – handles vector-database initialisation, upserting,
and querying against a Pinecone serverless index.
"""

from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore

from config import (
    PINECONE_API_KEY,
    PINECONE_ENVIRONMENT,
    PINECONE_INDEX,
    EMBEDDING_DIMENSION,
)
from services.embedding_service import get_embeddings


_pc_client = None
_vectorstore = None


def _get_client() -> Pinecone:
    """Return a singleton Pinecone client."""
    global _pc_client
    if _pc_client is None:
        _pc_client = Pinecone(api_key=PINECONE_API_KEY)
    return _pc_client


def ensure_index_exists() -> None:
    """Create the Pinecone index if it does not already exist."""
    pc = _get_client()
    existing = [idx.name for idx in pc.list_indexes()]
    if PINECONE_INDEX not in existing:
        pc.create_index(
            name=PINECONE_INDEX,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT),
        )


def get_vectorstore() -> PineconeVectorStore:
    """Return a singleton LangChain PineconeVectorStore instance."""
    global _vectorstore
    if _vectorstore is None:
        ensure_index_exists()
        _vectorstore = PineconeVectorStore(
            index_name=PINECONE_INDEX,
            embedding=get_embeddings(),
            pinecone_api_key=PINECONE_API_KEY,
        )
    return _vectorstore


def upsert_documents(documents: list) -> None:
    """Add a list of LangChain Document objects to the vector store."""
    vs = get_vectorstore()
    vs.add_documents(documents)


def similarity_search(query: str, k: int = 5) -> list:
    """Return the top-k most similar documents for *query*."""
    vs = get_vectorstore()
    return vs.similarity_search(query, k=k)
