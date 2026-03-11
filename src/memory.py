"""
Conversation memory manager – provides per-session chat message
history using modern LangChain ChatMessageHistory.
"""

from langchain_core.chat_history import InMemoryChatMessageHistory

_sessions: dict[str, InMemoryChatMessageHistory] = {}


def get_memory(session_id: str) -> InMemoryChatMessageHistory:
    """Return (or create) a ChatMessageHistory for *session_id*."""
    if session_id not in _sessions:
        _sessions[session_id] = InMemoryChatMessageHistory()
    return _sessions[session_id]


def get_chat_history(session_id: str) -> list:
    """Return the list of messages for *session_id*."""
    memory = get_memory(session_id)
    return memory.messages


def clear_memory(session_id: str) -> None:
    """Clear memory for the given session."""
    if session_id in _sessions:
        _sessions[session_id].clear()
        del _sessions[session_id]
