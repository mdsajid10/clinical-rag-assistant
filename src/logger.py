"""
Logger module – logs all user queries and assistant responses
to a rotating log file.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone

from config import LOG_DIR

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

_LOG_FILE = os.path.join(LOG_DIR, "queries.log")

# Configure logger
_logger = logging.getLogger("clinical_rag")
_logger.setLevel(logging.INFO)

_handler = RotatingFileHandler(
    _LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
_handler.setFormatter(
    logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
)
_logger.addHandler(_handler)


def log_query(session_id: str, question: str) -> None:
    """Log an incoming user question."""
    _logger.info(
        "SESSION=%s | QUERY=%s",
        session_id,
        question.replace("\n", " "),
    )


def log_response(session_id: str, answer: str) -> None:
    """Log the assistant's response."""
    _logger.info(
        "SESSION=%s | RESPONSE=%s",
        session_id,
        answer[:500].replace("\n", " "),
    )
