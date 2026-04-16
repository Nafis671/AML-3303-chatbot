# Technical Specification — SupportBot Studio (AI-Powered Customer Support Assistant)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [User Flow](#3-user-flow)
4. [RAG Workflow](#4-rag-workflow)
5. [Database Schema](#5-database-schema)
6. [Backend — Flask API](#6-backend--flask-api)
7. [Frontend — Streamlit UI](#7-frontend--streamlit-ui)
8. [Tech Stack & Dependencies](#8-tech-stack--dependencies)
9. [API Reference](#9-api-reference)
10. [Security Considerations](#10-security-considerations)
11. [Known Limitations & Future Work](#11-known-limitations--future-work)

---

## 1. Project Overview

**SupportBot Studio** is an AI-powered customer support Q&A assistant. Support teams upload knowledge-base documents (PDF, TXT, or JSON) — such as FAQs, product manuals, and policy documents — and customers ask natural-language questions. The system retrieves the most relevant passages from those documents and generates a grounded answer using an LLM, ensuring every response is anchored to the organisation's own support content rather than the model's training data.

The system is built around the **Retrieval-Augmented Generation (RAG)** pattern: instead of relying on a language model's training data, each answer is constructed from chunks of the user's own documents, retrieved via vector similarity search.

**Core capabilities:**

- Multi-user authentication (register / login)
- Per-user document upload, ingestion, and deletion
- FAISS-backed vector similarity search
- OpenAI LLM-generated answers grounded in document context
- Persistent per-user chat history
- Streamlit chat interface

---

## 2. System Architecture

![System Architecture](chatbot_diagrams/Architecture.drawio.svg)

The system follows a **three-tier architecture** connected via REST API over HTTP.

### 2.1 Frontend Layer

The Streamlit frontend (`frontend/streamlit_app_v3.13.py`) serves two logical surfaces:

- **Auth Pages** — login and registration screens rendered before any session is established.
- **Dashboard / Chat Interface** — the main application surface, accessible only after successful authentication. Includes the document upload sidebar and the chat window.

All communication from the frontend to the backend is done via synchronous `requests` calls to the Flask REST API at `http://127.0.0.1:5000`.

### 2.2 Backend Layer

The Flask backend (`backend/app.py`) orchestrates all application logic through a set of REST endpoints:

| Module | Responsibility |
|---|---|
| `app.py` | Route definitions, request validation, response formatting |
| `rag_pipeline.py` | Orchestrates the query path: embed → retrieve → prompt → LLM |
| `ingest.py` | Document loading, text chunking, embedding, and vector store insertion |
| `embeddings.py` | Thin wrapper around OpenAI's Embeddings API |
| `vector_store.py` | In-memory FAISS index with per-user metadata filtering |
| `db.py` | SQLite operations for users, chat history, and document records |

### 2.3 Data & Infrastructure Layer

| Store | Technology | Purpose |
|---|---|---|
| Relational DB | SQLite (`chat_history.db`) | Users, chat messages, document records |
| Vector Store | FAISS `IndexFlatL2` (in-memory) | Embedding vectors for similarity search |
| File Storage | Local filesystem | Raw uploaded document files |
| LLM API | OpenAI (`gpt-4o-mini`) | Response generation |
| Embeddings API | OpenAI (`text-embedding-3-small`) | 1536-dimensional text embeddings |

> **Note:** The FAISS index is in-memory only — it does not persist across backend restarts. Documents must be re-ingested if the server is restarted.

---

## 3. User Flow

![User Flow](chatbot_diagrams/user_flow.drawio.svg)

The diagram above captures two distinct interaction flows within the application.

### 3.1 Admin / Support User Flow

This flow describes how an internal user manages the knowledge base and reviews conversations:

1. **Sign Up** — The user creates a new account via the registration form. The backend validates the credentials (username ≥ 3 characters, password ≥ 6 characters) and stores a SHA-256 hashed password in SQLite.
2. **Login** — On subsequent visits the user authenticates. A successful login sets `st.session_state.logged_in = True` and stores the username in session state.
3. **Dashboard** — The authenticated user lands on the main application view.
4. **Upload Documents** — From the sidebar the user drops a PDF, TXT, or JSON file. The frontend saves the file locally, then calls `POST /upload`. The backend parses, chunks, embeds, and indexes the document.
5. **View / Review Conversations** — Chat history is loaded on login via `GET /history` and is displayed in the main chat area.

### 3.2 Customer / End-User Chat Flow

This flow describes the question-answering interaction:

1. **Ask Question** — The user types a question and clicks Send.
2. **RAG Search** — The backend embeds the query and runs FAISS similarity search against the user's indexed document chunks.
3. **Generate Answer** — The retrieved chunks are assembled into a prompt and sent to the OpenAI LLM, which generates a grounded response.
4. **Follow-up** — The user may ask follow-up questions; the session persists in `st.session_state.chat`.
5. **No Answer → Fallback** — If no relevant chunks are found, the system returns a canned message advising the user to upload a document first.

---

## 4. RAG Workflow

![RAG Workflow](chatbot_diagrams/RAG_workflow.drawio.svg)

The RAG workflow is divided into two pipelines that share the same vector store.

### 4.1 Document Ingestion Pipeline

Triggered when a user uploads a document via `POST /upload`.

```
Upload file
    └─► load_file()       [ingest.py]   — parse PDF/TXT/JSON into raw text
    └─► chunk_text()      [ingest.py]   — split into 500-character chunks
    └─► get_embedding()   [ingest.py]   — call OpenAI text-embedding-3-small (1536-dim)
    └─► VectorStore.add() [vector_store.py] — store vector + text + {username, filename} metadata
    └─► mark_document_embedded() [db.py] — update SQLite document record
```

**Chunking strategy:** Simple fixed-size character slicing at 500 characters. Each chunk is independently embedded — no overlap or sentence-boundary awareness.

**Metadata tagging:** Every vector is tagged with `username` and `filename`. This enables per-user isolation at query time and selective deletion by document.

### 4.2 Query Pipeline

Triggered when a user sends a message via `POST /chat`.

```
User question
    └─► get_embedding()         [embeddings.py]  — embed the query
    └─► VectorStore.search()    [vector_store.py] — FAISS L2 search, filtered by username, top-k=3
    └─► Build prompt            [rag_pipeline.py] — join chunks as context
    └─► client.chat.completions [OpenAI]          — call gpt-4o-mini with system + user message
    └─► Return response         [app.py]          — save both turns to SQLite, return JSON
```

**System prompt constraint:** The LLM is instructed to answer *only* from the provided context and to say it doesn't know if the context is insufficient. This prevents hallucination.

**Similarity search detail:** FAISS `IndexFlatL2` performs exact L2-distance search. The search fetches `min(total_chunks, k×10)` candidates and then filters down to `k=3` results matching the requesting user's `username`.

### 4.3 Cross-Pipeline Link

The vectors stored during ingestion are the same vectors queried at chat time. The `VectorStore` object is instantiated once at server startup and held in memory for the process lifetime, making both pipelines share a single live index.

---

## 5. Database Schema

![Entity Relationship Diagram](chatbot_diagrams/ERD.drawio.svg)

The application uses **SQLite** with three tables. The ERD above shows the full intended relational design; below is the implemented schema as defined in `backend/db.py`.

### 5.1 `users`

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `username` | TEXT | UNIQUE NOT NULL |
| `password` | TEXT | NOT NULL (SHA-256 hex digest) |

### 5.2 `chats`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `username` | TEXT | Foreign reference to users.username |
| `role` | TEXT | `"user"` or `"assistant"` |
| `message` | TEXT | Raw message content |

### 5.3 `documents`

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `username` | TEXT | NOT NULL |
| `filename` | TEXT | NOT NULL |
| `file_path` | TEXT | NOT NULL |
| `is_embedded` | INTEGER | DEFAULT 0 (boolean flag) |
| — | — | UNIQUE(username, filename) |

### 5.4 Relationships

```
users ──< chats       (one user → many chat messages)
users ──< documents   (one user → many uploaded documents)
```

> The full ERD also models `Organization`, `KnowledgeBase`, `DocumentChunk`, `Conversation`, and `Message` entities (see diagram), which represent the intended production schema. The current implementation uses a simplified SQLite schema as a prototype.

---

## 6. Backend — Flask API

Entry point: `backend/app.py`. The server runs on `http://127.0.0.1:5000` with Flask's development server (`debug=True`, `use_reloader=False`).

### Module Responsibilities

#### `ingest.py`

- `resolve_path(file_path)` — normalises absolute vs. relative paths against the project root.
- `load_file(file_path)` — dispatches to PDF (`pypdf.PdfReader`), TXT (plain read), or JSON (`json.load` → `json.dumps`) parsers.
- `chunk_text(text, chunk_size=500)` — character-level sliding window chunking.
- `ingest_document(file_path, vector_store, client, username)` — orchestrates load → chunk → embed → store, returns chunk count.

#### `embeddings.py`

- `get_embedding(text, client)` — calls `text-embedding-3-small`, returns a 1536-float list.

#### `vector_store.py` — `VectorStore`

| Method | Description |
|---|---|
| `__init__(dim=1536)` | Creates `faiss.IndexFlatL2(1536)`, initialises `texts`, `metadata`, `_embeddings` lists |
| `add(embedding, text, username, filename)` | Adds vector to FAISS index and appends to parallel lists |
| `search(query_embedding, k=3, username)` | Searches top `k×10` candidates, filters by username, returns top-`k` texts |
| `delete_by_filename(filename, username)` | Rebuilds FAISS index excluding all chunks from the target document |

#### `db.py`

Provides CRUD wrappers over SQLite: `init_db`, `register_user`, `login_user`, `save_document`, `mark_document_embedded`, `get_user_documents`, `delete_document`, `save_message`, `load_chat_history`, `clear_chat_history`.

#### `rag_pipeline.py`

- `answer_question(question, vector_store, client, username)` — full query pipeline: embed → search → build prompt → call `gpt-4o-mini` → return string response.

---

## 7. Frontend — Streamlit UI

Entry point: `frontend/streamlit_app_v3.13.py`.

### Session State Keys

| Key | Type | Purpose |
|---|---|---|
| `logged_in` | bool | Guards all authenticated views |
| `username` | str | Passed with every API request |
| `chat` | list[tuple] | In-memory chat history for the current session |
| `loaded` | bool | Prevents re-fetching history on every rerender |
| `auth_mode` | str | `"Login"` or `"Register"` toggle |
| `pending_file` | str \| None | Filename of a staged but not yet uploaded file |
| `pending_file_path` | str \| None | Absolute path of the staged file |
| `uploader_key` | int | Incremented to reset the file uploader widget after upload |

### UI Sections

```
┌─────────────────────────────────────────────┐
│  Auth Screen (if not logged_in)             │
│  ┌────────────────────────────────────┐     │
│  │ Login / Register form (centred)    │     │
│  └────────────────────────────────────┘     │
├─────────────────────────────────────────────┤
│  Sidebar            │  Main Area            │
│  ─ Upload section   │  ─ Top bar (title,    │
│  ─ Uploaded docs    │    user badge)        │
│    list + delete    │  ─ Logout / Clear     │
│                     │  ─ Chat bubble area   │
│                     │  ─ Input + Send       │
└─────────────────────────────────────────────┘
```

### Upload Flow (Frontend Side)

1. `st.file_uploader` stores the file bytes in memory.
2. On selection, the file is written to `frontend/data/raw_docs/<filename>` on disk.
3. A staged filename is shown with a confirm **Upload** button.
4. On confirm, a visual progress bar animates through `Reading → Chunking → Embedding` stages, then `POST /upload` is called.
5. On success, `uploader_key` is incremented to reset the widget; the document list refreshes.

### Chat Flow (Frontend Side)

1. User types in `st.text_input` and clicks **Send**.
2. `POST /chat` is called with `{message, username}`.
3. The response tuple `("user", input)` and `("assistant", reply)` are appended to `st.session_state.chat`.
4. `st.rerun()` rerenders the bubble list with the new messages.

---

## 8. Tech Stack & Dependencies

| Package | Version Pinned | Role |
|---|---|---|
| `flask` | No | REST API server |
| `streamlit` | No | Frontend UI framework |
| `openai` | No | LLM + Embeddings API client |
| `faiss-cpu` | No | In-memory vector similarity search |
| `pypdf` | No | PDF text extraction |
| `numpy` | No | Array manipulation for FAISS vectors |
| `tiktoken` | No | Token counting (imported but not actively used in current pipeline) |
| `python-dotenv` | No | Loads `OPENAI_API_KEY` from `.env` |
| `requests` | No | Frontend → backend HTTP calls |
| `sqlite3` | stdlib | Relational data persistence |
| `hashlib` | stdlib | SHA-256 password hashing |

**OpenAI models used:**

| Purpose | Model |
|---|---|
| Text embeddings | `text-embedding-3-small` (1536 dimensions) |
| Answer generation | `gpt-4o-mini` |

---

## 9. API Reference

All endpoints accept and return `application/json`.

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/register` | — | Create a new user account |
| `POST` | `/login` | — | Authenticate and start session |
| `POST` | `/upload` | username | Parse, chunk, embed, and index a document |
| `POST` | `/chat` | username | Submit a question and receive an LLM answer |
| `GET` | `/history` | username | Retrieve full chat history for a user |
| `GET` | `/documents` | username | List all uploaded documents for a user |
| `DELETE` | `/documents/delete` | username | Remove a document from vector store and DB |
| `DELETE` | `/clear-history` | username | Wipe all chat messages for a user |

### Request / Response Shapes

**`POST /register`**
```json
// Request
{ "username": "alice", "password": "secret123" }

// Response 200
{ "message": "Account created! Welcome, alice." }

// Response 409
{ "error": "Username already taken" }
```

**`POST /chat`**
```json
// Request
{ "message": "What is the refund policy?", "username": "alice" }

// Response 200
{ "response": "According to the uploaded document, refunds are processed within 5–7 business days." }
```

**`POST /upload`**
```json
// Request
{ "file_path": "/absolute/path/to/document.pdf", "username": "alice" }

// Response 200
{ "message": "Indexed successfully", "chunks": 42 }
```

---

## 10. Security Considerations

| Area | Current Approach | Risk / Gap |
|---|---|---|
| Password storage | SHA-256 hex digest | No salt — vulnerable to rainbow table attacks. Should use `bcrypt` or `argon2`. |
| Authentication | Session state in Streamlit (client-side) | No server-side session tokens. Username is passed as a plain parameter in every request — spoofable. |
| File validation | Extension check (`.pdf`, `.txt`, `.json`) | No MIME type or content validation. Malicious files with a valid extension are accepted. |
| API authorisation | Username passed as request body/param | No token-based auth; any client can query any user's history by supplying their username. |
| HTTPS | None (localhost HTTP) | All traffic is plaintext on `127.0.0.1`. |
| Vector store isolation | Username metadata filter | Isolation is enforced by application logic, not by the store itself. A bug in the filter would expose all users' data. |

---

## 11. Known Limitations & Future Work

| Limitation | Impact | Suggested Resolution |
|---|---|---|
| FAISS index is in-memory only | All document embeddings are lost on server restart | Persist the index to disk (`faiss.write_index`) or migrate to a persistent vector DB (e.g. Chroma, Qdrant) |
| Fixed 500-character chunking | Chunks may split mid-sentence, degrading retrieval quality | Use sentence-aware or recursive chunking (e.g. LangChain `RecursiveCharacterTextSplitter`) |
| No conversation context window | LLM does not see prior turns — cannot answer follow-up questions that reference earlier exchanges | Pass recent message history as additional context in the prompt |
| Single-process Flask dev server | Not suitable for concurrent users | Deploy with Gunicorn or uWSGI; consider async frameworks |
| No token/session authentication | Security risk in multi-user deployment | Implement JWT or session-cookie auth |
| `tiktoken` imported but unused | Dead dependency | Either integrate token-aware chunking or remove from requirements |
| No document persistence across restarts | Embeddings re-ingest required after every restart | Persist FAISS index and reload on startup |
