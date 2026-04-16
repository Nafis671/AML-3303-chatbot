from pypdf import PdfReader
import os
import json

# =========================
# PATH RESOLUTION
# =========================


def resolve_path(file_path):
    if os.path.isabs(file_path):
        return file_path
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    fixed_path = os.path.join(base_dir, "frontend", file_path)
    return fixed_path


# =========================
# FILE LOADER (pdf / txt / json)
# =========================
def load_file(file_path):
    file_path = resolve_path(file_path)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        reader = PdfReader(file_path)
        return "".join(page.extract_text() or "" for page in reader.pages)

    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif ext == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Flatten JSON to string
        return json.dumps(data, indent=2)

    else:
        raise ValueError(
            f"Unsupported file type: {ext}. Use PDF, TXT, or JSON.")


# =========================
# CHUNKING
# =========================
def chunk_text(text, chunk_size=500):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]


# =========================
# MAIN INGEST FUNCTION
# =========================
def ingest_document(file_path, vector_store, client, username=None):
    text = load_file(file_path)
    chunks = chunk_text(text)
    filename = os.path.basename(file_path)

    for chunk in chunks:
        embedding = get_embedding(chunk, client)
        vector_store.add(embedding, chunk, username=username,
                         filename=filename)  # NEW: pass metadata

    return len(chunks)


# =========================
# EMBEDDING FUNCTION
# =========================
def get_embedding(text, client):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding
