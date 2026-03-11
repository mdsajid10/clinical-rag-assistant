<div align="center">

# 🏥 Clinical RAG Assistant

### AI-Powered Medical Knowledge Chatbot

A production-grade **Retrieval-Augmented Generation** system that answers medical questions
using evidence from clinical PDF documents — with source citations, hybrid search, and a premium ChatGPT-style UI.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask)](https://flask.palletsprojects.com)
[![LangChain](https://img.shields.io/badge/LangChain-LCEL-1C3C3C?logo=langchain)](https://langchain.com)
[![Pinecone](https://img.shields.io/badge/Pinecone-Vector_DB-000000)](https://pinecone.io)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3-F55036)](https://groq.com)

</div>

---

## 📸 Screenshots

<div align="center">

| Landing Page | Chat Interface |
|:---:|:---:|
| ![Landing](static/screenshots/landing.png) | ![Chat](static/screenshots/chat.png) |

</div>

> _Replace the screenshot paths above with actual screenshots from your deployment._

---

## ✨ Features

### Core RAG Pipeline
- 📄 **PDF Ingestion** — Load medical PDFs, split into chunks, generate embeddings
- 🔍 **Hybrid Retrieval** — Combines Pinecone vector search + BM25 keyword search using Reciprocal Rank Fusion
- 🤖 **LLM-Powered Answers** — Groq Llama 3.3 (70B) generates contextual, cited responses
- 💬 **Conversation Memory** — Remembers context across messages in the same session
- 📎 **Source Citations** — Every answer includes clickable references to source documents and page numbers

### Premium Chat UI
- 🎨 **Modern Dark Theme** — Glassmorphism design inspired by ChatGPT / Perplexity
- ⏳ **"Assistant is thinking…"** — Animated loading indicator with pulsing dots
- 📂 **Collapsible Sources** — Clean answers with expandable evidence panel
- 🔗 **Clickable PDF Links** — Open source PDFs at the exact cited page
- 🕐 **Message Timestamps** — Every message shows when it was sent
- 📱 **Fully Responsive** — Works on desktop, tablet, and mobile

### Document Management
- 📤 **Drag-and-Drop Upload** — Upload PDFs from the browser with progress indicator
- 📚 **Knowledge Base Panel** — Sidebar displays all indexed documents
- 🔄 **Auto-Indexing** — Uploaded documents are automatically chunked, embedded, and indexed

### Developer Tools
- 🛠️ **Debug Panel** — Toggle to view retrieved chunks with similarity scores
- 📊 **Evaluation Pipeline** — Keyword overlap + semantic similarity scoring
- 📝 **JSON Query Logging** — Every interaction logged with full context to `logs/chat_logs.json`

---

## 🏗️ Architecture

```
User Question
     │
     ▼
┌─────────────┐     ┌──────────────┐
│  Flask App  │────▶│  RAG Chain   │
└─────────────┘     └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Memory  │ │ Hybrid   │ │  Groq    │
        │ (Session)│ │ Retriever│ │ Llama 3.3│
        └──────────┘ └────┬─────┘ └──────────┘
                          │
                ┌─────────┼─────────┐
                ▼                   ▼
          ┌──────────┐        ┌──────────┐
          │ Pinecone │        │   BM25   │
          │ (Vector) │        │(Keyword) │
          └──────────┘        └──────────┘
```

---

## 📁 Project Structure

```
clinical-rag-assistant/
│
├── app.py                          # Flask application (routes & API)
├── config.py                       # Environment variables & constants
├── ingest.py                       # PDF ingestion pipeline
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker container setup
├── .env.example                    # Environment variable template
│
├── src/
│   ├── rag_chain.py                # RAG pipeline (LCEL chain + streaming)
│   ├── retriever.py                # Pinecone vector retriever
│   ├── hybrid_retriever.py         # BM25 + Vector hybrid search (RRF)
│   ├── memory.py                   # Session-based conversation memory
│   ├── chat_logger.py              # Structured JSON logging
│   └── logger.py                   # Query/response file logger
│
├── services/
│   ├── llm_service.py              # Groq LLM factory
│   ├── embedding_service.py        # HuggingFace embedding wrapper
│   └── pinecone_service.py         # Pinecone vector store manager
│
├── templates/
│   └── chat.html                   # Premium chat interface
│
├── static/
│   ├── style.css                   # Glassmorphism dark theme CSS
│   ├── script.js                   # Chat UI logic (streaming, upload, etc.)
│   └── pdfs/                       # Served PDFs for clickable links
│
├── evaluation/
│   ├── test_questions.json         # Sample questions + expected answers
│   └── evaluate.py                 # Evaluation script (keyword + semantic)
│
├── data/                           # Source PDF documents
├── logs/                           # Query logs (auto-created)
├── uploads/                        # Temp upload storage (auto-created)
│
└── .github/
    └── workflows/
        └── deploy.yml              # CI/CD pipeline (GitHub Actions)
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [Groq API Key](https://console.groq.com/keys) (free)
- [Pinecone API Key](https://app.pinecone.io/) (free tier available)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/clinical-rag-assistant.git
cd clinical-rag-assistant
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
GROQ_API_KEY=gsk_your_groq_key_here
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX=clinical-rag-chatbot
```

### 4. Add Medical PDFs

Place your PDF documents in the `data/` folder.

### 5. Run Ingestion

```bash
python ingest.py
```

This will:
- Load all PDFs from `data/`
- Split them into chunks (500 chars, 50 overlap)
- Generate embeddings using `all-MiniLM-L6-v2`
- Upload vectors to Pinecone
- Copy PDFs to `static/pdfs/` for clickable links

### 6. Start the Server

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## 📤 Uploading Documents

You can upload PDFs in **two ways**:

1. **From the UI** — Drag and drop a PDF into the sidebar upload zone
2. **Manually** — Place PDFs in `data/` and run `python ingest.py`

Uploaded documents are automatically:
- Saved to `data/`
- Chunked and embedded
- Indexed in Pinecone
- Added to the Knowledge Base panel

---

## 📊 Running Evaluation

```bash
python evaluation/evaluate.py
```

This runs 10 medical questions through the RAG pipeline and measures:

| Metric | Description |
|--------|-------------|
| **Keyword Score** | % of expected keywords found in the answer |
| **Semantic Score** | Cosine similarity between answer and expected answer embeddings |
| **Response Time** | Time taken per question |

Results are saved to `evaluation/results.json`.

---

## 🛠️ Debug Mode

Click the **📊 chart icon** in the header to enable Debug Mode.

When enabled, each response shows:
- Retrieved chunk content (truncated)
- Source document and page number
- Similarity score

---

## 🐳 Docker

```bash
docker build -t clinical-rag-assistant .
docker run -p 5000:5000 --env-file .env clinical-rag-assistant
```

---

## ⚙️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.10 |
| **Backend** | Flask |
| **LLM** | Groq — Llama 3.3 70B Versatile |
| **Orchestration** | LangChain (LCEL) |
| **Vector Database** | Pinecone (Serverless) |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` |
| **Keyword Search** | BM25 (rank-bm25) |
| **Frontend** | HTML, CSS, JavaScript |
| **Deployment** | Docker, AWS EC2, GitHub Actions |

---

## 📜 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serve the chat UI |
| `POST` | `/chat` | Non-streaming chat |
| `POST` | `/chat/stream` | Streaming chat (SSE) |
| `POST` | `/upload` | Upload and ingest a PDF |
| `POST` | `/reset` | Clear session memory |
| `GET` | `/api/documents` | List indexed documents |
| `GET` | `/static/pdfs/<file>` | Serve a PDF file |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## ⚠️ Disclaimer

> This assistant retrieves information from medical documents. It is intended for **educational and research purposes only**. Always consult qualified healthcare professionals for medical advice, diagnosis, or treatment.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<div align="center">

**Built with ❤️ using Groq, Pinecone, and LangChain**

</div>
