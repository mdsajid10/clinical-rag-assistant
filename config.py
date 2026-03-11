"""
Configuration module for Clinical RAG Assistant.
Loads environment variables and defines application constants.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── OpenAI ──────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o"
OPENAI_TEMPERATURE = 0.2

# ── Groq ────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ── Pinecone ────────────────────────────────────────────────────────────
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "clinical-rag-chatbot")

# ── Embeddings ──────────────────────────────────────────────────────────
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# ── Document splitting ─────────────────────────────────────────────────
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# ── Retrieval ───────────────────────────────────────────────────────────
TOP_K = 5

# ── Paths ───────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")

# ── System prompt ───────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are a clinical medical assistant.\n"
    "Answer only using the provided context.\n"
    "If the answer cannot be found, say that the information is not available.\n"
    "Always cite the document and page number used in the answer."
)
