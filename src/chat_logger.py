"""
Structured JSON logger – logs every chat interaction with full context
to logs/chat_logs.json for auditing and analysis.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from config import LOG_DIR

_LOG_FILE = os.path.join(LOG_DIR, "chat_logs.json")

# Ensure directory exists
os.makedirs(LOG_DIR, exist_ok=True)


def log_interaction(
    session_id: str,
    user_question: str,
    retrieved_documents: list[dict],
    model_response: str,
) -> None:
    """
    Append a structured JSON entry to the chat log file.
    Each entry contains timestamp, question, retrieved docs, and response.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "user_question": user_question,
        "retrieved_documents": retrieved_documents,
        "model_response": model_response,
    }

    # Read existing log
    entries: list[dict] = []
    if os.path.exists(_LOG_FILE):
        try:
            with open(_LOG_FILE, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except (json.JSONDecodeError, IOError):
            entries = []

    entries.append(entry)

    with open(_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
