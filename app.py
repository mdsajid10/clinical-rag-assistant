"""
Clinical RAG Assistant – Flask application.
Serves the chat UI, handles streaming chat, PDF upload,
and debug info endpoints.
"""

import os
import uuid

from flask import (
    Flask, render_template, request, jsonify, Response, session,
    send_from_directory,
)
from werkzeug.utils import secure_filename

from config import DATA_DIR
from src.rag_chain import ask, ask_stream
from src.memory import clear_memory
from ingest import ingest_single_file, STATIC_PDF_DIR
from src.hybrid_retriever import rebuild_bm25_index

app = Flask(__name__)
app.secret_key = uuid.uuid4().hex

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_PDF_DIR, exist_ok=True)


# ── Page Routes ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the chat interface."""
    if "session_id" not in session:
        session["session_id"] = uuid.uuid4().hex
    return render_template("chat.html")


# ── Chat Routes ──────────────────────────────────────────────────────────

@app.route("/chat", methods=["POST"])
def chat():
    """Non-streaming chat endpoint."""
    data = request.get_json(force=True)
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "No question provided"}), 400

    sid = session.get("session_id", "anonymous")
    result = ask(question, session_id=sid)
    return jsonify(result)


@app.route("/chat/stream", methods=["POST"])
def chat_stream():
    """Streaming chat endpoint using Server-Sent Events."""
    data = request.get_json(force=True)
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "No question provided"}), 400

    sid = session.get("session_id", "anonymous")

    def generate():
        yield from ask_stream(question, session_id=sid)

    return Response(generate(), mimetype="text/event-stream")


@app.route("/reset", methods=["POST"])
def reset():
    """Clear conversation memory for the current session."""
    sid = session.get("session_id", "anonymous")
    clear_memory(sid)
    return jsonify({"status": "ok"})


# ── PDF Upload Route ─────────────────────────────────────────────────────

@app.route("/upload", methods=["POST"])
def upload_pdf():
    """
    Upload a PDF, save it, ingest it into Pinecone,
    and rebuild the BM25 index.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are accepted"}), 400

    filename = secure_filename(file.filename)

    # Save to data/ folder and uploads/ folder
    data_path = os.path.join(DATA_DIR, filename)
    file.save(data_path)

    # Ingest the single PDF
    result = ingest_single_file(data_path)

    if result["status"] == "ok":
        # Rebuild BM25 index with new data
        try:
            rebuild_bm25_index()
        except Exception:
            pass  # Non-critical if BM25 rebuild fails

    return jsonify(result)


# ── Knowledge Base Route ─────────────────────────────────────────────────

@app.route("/api/documents")
def list_documents():
    """List all indexed PDF documents for the knowledge base panel."""
    docs = set()
    for folder in [DATA_DIR, STATIC_PDF_DIR]:
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                if f.lower().endswith(".pdf"):
                    docs.add(f)
    return jsonify(sorted(docs))


# ── PDF Serving Route ────────────────────────────────────────────────────

@app.route("/static/pdfs/<path:filename>")
def serve_pdf(filename):
    """Serve uploaded/ingested PDFs for clickable source links."""
    return send_from_directory(STATIC_PDF_DIR, filename)


# ── Entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug)
