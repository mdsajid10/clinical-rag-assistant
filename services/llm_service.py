"""
LLM service – provides streaming and non-streaming Groq instances.
"""

from langchain_groq import ChatGroq
from config import OPENAI_TEMPERATURE, GROQ_API_KEY


def get_llm(streaming: bool = False):
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=OPENAI_TEMPERATURE,
        groq_api_key=GROQ_API_KEY,
        streaming=streaming,
    )