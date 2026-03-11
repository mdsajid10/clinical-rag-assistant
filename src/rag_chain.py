"""
RAG chain module – builds the conversational retrieval pipeline
using modern LangChain LCEL, combining hybrid retriever, memory,
streaming LLM, debug info, and structured logging.
"""

from __future__ import annotations

import json
from typing import Generator

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.callbacks import BaseCallbackHandler

from config import SYSTEM_PROMPT, TOP_K
from services.llm_service import get_llm
from src.memory import get_memory, get_chat_history
from src.hybrid_retriever import hybrid_retrieve
from src.retriever import format_context, format_sources
from src.logger import log_query, log_response
from src.chat_logger import log_interaction


# ── Streaming callback ──────────────────────────────────────────────────

class _TokenCollector(BaseCallbackHandler):
    """Collects streamed tokens into a list so they can be yielded."""

    def __init__(self):
        self.tokens: list[str] = []

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.tokens.append(token)


# ── Prompt ───────────────────────────────────────────────────────────────

_QA_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ]
)


# ── Helpers ──────────────────────────────────────────────────────────────

def _build_debug_chunks(chunks) -> list[dict]:
    """Build serializable debug info from retrieved chunks."""
    return [
        {
            "content": c.content[:300],
            "source": c.source_document,
            "page": c.page_number,
            "score": round(c.score, 4) if c.score else None,
        }
        for c in chunks
    ]


# ── Public API ───────────────────────────────────────────────────────────

def ask(question: str, session_id: str) -> dict:
    """
    Non-streaming: answer a question and return the full result.
    Returns {"answer": str, "sources": list[dict], "debug_chunks": list[dict]}.
    """
    log_query(session_id, question)

    # Hybrid retrieve context
    chunks = hybrid_retrieve(question, k=TOP_K)
    context = format_context(chunks)
    sources = format_sources(chunks)
    debug_chunks = _build_debug_chunks(chunks)

    # Build chain
    llm = get_llm(streaming=False)
    chat_history = get_chat_history(session_id)

    chain = _QA_PROMPT | llm | StrOutputParser()

    try:
        answer = chain.invoke({
            "context": context,
            "question": question,
            "chat_history": chat_history,
        })
    except Exception as exc:
        answer = f"Error: {exc}"

    # Save to memory
    memory = get_memory(session_id)
    memory.add_user_message(question)
    memory.add_ai_message(answer)

    log_response(session_id, answer)

    # Structured JSON log
    log_interaction(
        session_id=session_id,
        user_question=question,
        retrieved_documents=sources,
        model_response=answer,
    )

    return {"answer": answer, "sources": sources, "debug_chunks": debug_chunks}


def ask_stream(question: str, session_id: str) -> Generator[str, None, None]:
    """
    Streaming: yield tokens as they are generated, followed by a final
    JSON object with source citations and debug info.
    """
    log_query(session_id, question)

    # Hybrid retrieve context
    chunks = hybrid_retrieve(question, k=TOP_K)
    context = format_context(chunks)
    sources = format_sources(chunks)
    debug_chunks = _build_debug_chunks(chunks)

    # Build chain with streaming LLM
    llm = get_llm(streaming=True)
    chat_history = get_chat_history(session_id)

    chain = _QA_PROMPT | llm | StrOutputParser()

    # Collect streamed tokens
    collector = _TokenCollector()
    try:
        answer = chain.invoke(
            {
                "context": context,
                "question": question,
                "chat_history": chat_history,
            },
            config={"callbacks": [collector]},
        )
    except Exception as exc:
        error_msg = str(exc)
        if "insufficient_quota" in error_msg or "429" in error_msg:
            friendly = (
                "⚠️ API quota exceeded. Please check your billing "
                "and add credits, then try again."
            )
        elif "decommissioned" in error_msg:
            friendly = "⚠️ The LLM model has been decommissioned. Please update the model name in config."
        else:
            friendly = f"⚠️ An error occurred: {error_msg}"
        yield f"data: {json.dumps({'token': friendly})}\n\n"
        yield f"data: {json.dumps({'done': True, 'sources': [], 'debug_chunks': []})}\n\n"
        log_response(session_id, f"ERROR: {error_msg}")
        return

    # Yield tokens one by one
    for token in collector.tokens:
        yield f"data: {json.dumps({'token': token})}\n\n"

    # Save to memory
    memory = get_memory(session_id)
    memory.add_user_message(question)
    memory.add_ai_message(answer)

    log_response(session_id, answer)

    # Structured JSON log
    log_interaction(
        session_id=session_id,
        user_question=question,
        retrieved_documents=sources,
        model_response=answer,
    )

    # Final event with sources and debug
    yield f"data: {json.dumps({'done': True, 'sources': sources, 'debug_chunks': debug_chunks})}\n\n"
