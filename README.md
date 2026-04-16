# SupportBot Studio – AI-Powered Customer Support Chatbot Builder
A Retrieval-Augmented Generation (RAG) chatbot that lets users upload documents and ask questions about them. Built with Flask, OpenAI, and FAISS.

---

## Features

- **User authentication** — register and login with per-user data isolation
- **Document ingestion** — upload PDF, TXT, or JSON files and index them into a vector store
- **RAG-powered chat** — answers questions using only content from your uploaded documents
- **Chat history** — messages are persisted per user in a SQLite database
- **Document management** — list and delete uploaded documents
- **Streamlit UI** — optional frontend via `streamlit_app.py`

---

## Project Structure

```
├── app.py               # Flask API server (routes and app init)
├── db.py                # SQLite database helpers (users, chats, documents)
├── ingest.py            # File loading, chunking, and embedding ingestion
├── rag_pipeline.py      # RAG query pipeline (embed → retrieve → generate)
├── vector_store.py      # In-memory FAISS vector store with metadata filtering
├── embeddings.py        # OpenAI embedding helper
├── document_loader.py   # PDF text extraction (pypdf)
├── streamlit_app.py     # Streamlit frontend (optional)
├── utils.py             # Utility functions (currently empty)
├── chat_history.db      # SQLite database (auto-created on first run)
└── .env                 # Environment variables (not committed)
```

---

## Setup

### 1. Clone the repo and install dependencies

```bash
pip install flask openai faiss-cpu pypdf PyPDF2 python-dotenv streamlit numpy
```

### 2. Create a `.env` file

```
OPENAI_API_KEY=sk-...
```

### 3. Run the Flask server

```bash
python app.py
```

The server starts on `http://localhost:5000`.

### 4. (Optional) Run the Streamlit frontend

```bash
streamlit run streamlit_app.py
```

---

## API Reference

All requests and responses use JSON unless noted.

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/register` | Create a new account |
| `POST` | `/login` | Authenticate an existing user |

**Register / Login body:**
```json
{ "username": "alice", "password": "secret123" }
```

---

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Upload and index a document |
| `GET` | `/documents?username=alice` | List documents for a user |
| `DELETE` | `/documents/delete` | Delete a document |

**Upload body:**
```json
{ "file_path": "path/to/file.pdf", "username": "alice" }
```

**Delete body:**
```json
{ "username": "alice", "filename": "file.pdf" }
```

Supported file types: `.pdf`, `.txt`, `.json`

---

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Send a message and get a RAG answer |
| `GET` | `/history?username=alice` | Retrieve chat history |
| `DELETE` | `/clear-history` | Clear all messages for a user |

**Chat body:**
```json
{ "message": "What does the document say about pricing?", "username": "alice" }
```

**Clear history body:**
```json
{ "username": "alice" }
```

---

## How It Works

1. **Ingestion** — uploaded files are read, split into 500-character chunks, and each chunk is embedded using `text-embedding-3-small`. Embeddings are stored in an in-memory FAISS index with username and filename metadata.

2. **Retrieval** — when a user sends a message, it is embedded and the top-3 most similar chunks are retrieved, filtered to only the current user's documents.

3. **Generation** — the retrieved chunks are passed as context to `gpt-4o-mini`, which answers based only on that context. If no relevant chunks are found, the user is prompted to upload a document first.

---

## Notes & Limitations

- The vector store is **in-memory only** — all indexed documents are lost when the server restarts. You would need to re-upload files after a restart.
- Passwords are hashed with SHA-256 but there is no salting. For production use, switch to `bcrypt` or `argon2`.
- The Flask server runs in debug mode by default (`debug=True`). Disable this for production.
- File paths passed to `/upload` must be accessible on the server's filesystem.
