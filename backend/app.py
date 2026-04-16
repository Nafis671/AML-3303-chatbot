from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os

# =========================
# LOAD ENV FIRST
# =========================
load_dotenv()

# =========================
# OPENAI CLIENT
# =========================
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

client = OpenAI(api_key=api_key)

# =========================
# IMPORTS
# =========================
from ingest import ingest_document
from vector_store import VectorStore
from rag_pipeline import answer_question
from db import init_db, load_chat_history, save_message, register_user, login_user, clear_chat_history, save_document, mark_document_embedded, get_user_documents, delete_document

init_db()

# =========================
# APP INIT
# =========================
app = Flask(__name__)
vector_store = VectorStore()


# =========================
# AUTH: REGISTER
# =========================
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    success, msg = register_user(username, password)
    if success:
        return jsonify({"message": f"Account created! Welcome, {username}."})
    else:
        return jsonify({"error": msg}), 409


# =========================
# AUTH: LOGIN
# =========================
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    success, msg = login_user(username, password)
    if success:
        return jsonify({"message": "Login successful", "username": username})
    else:
        return jsonify({"error": msg}), 401


# =========================
# UPLOAD ENDPOINT
# =========================
@app.route("/upload", methods=["POST"])
def upload():
    data = request.json
    file_path = data["file_path"]
    username = data.get("username", "guest")
    filename = os.path.basename(file_path)

    # Validate file type
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".pdf", ".txt", ".json"]:
        return jsonify({"error": "Only PDF, TXT, and JSON files are supported"}), 400

    # Save doc record to DB (not embedded yet)
    save_document(username, filename, file_path)

    # Ingest into vector store with username metadata
    count = ingest_document(file_path, vector_store, client, username=username)

    # Mark as embedded
    mark_document_embedded(username, filename)

    return jsonify({"message": "Indexed successfully", "chunks": count})


# =========================
# CHAT ENDPOINT
# =========================
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_input = data["message"]
        username = data.get("username", "guest")

        answer = answer_question(user_input, vector_store, client, username=username)

        # Save both sides to DB
        save_message(username, "user", user_input)
        save_message(username, "assistant", answer)

        return jsonify({"response": answer})

    except Exception as e:
        print("CHAT ERROR:", e)
        return jsonify({"error": str(e)}), 500


# =========================
# HISTORY ENDPOINT
# =========================
@app.route("/history", methods=["GET"])
def history():
    username = request.args.get("username")
    return jsonify(load_chat_history(username))


# =========================
# DOCUMENTS: LIST
# =========================
@app.route("/documents", methods=["GET"])
def documents():
    username = request.args.get("username")
    if not username:
        return jsonify({"error": "Username required"}), 400
    return jsonify(get_user_documents(username))


# =========================
# DOCUMENTS: DELETE
# =========================
@app.route("/documents/delete", methods=["DELETE"])
def delete_doc():
    data = request.json
    username = data.get("username")
    filename = data.get("filename")
    if not username or not filename:
        return jsonify({"error": "Username and filename required"}), 400

    # Remove from vector store
    vector_store.delete_by_filename(filename, username)

    # Remove from DB
    delete_document(username, filename)

    return jsonify({"message": f"{filename} deleted"})


# =========================
# CLEAR HISTORY ENDPOINT
# =========================
@app.route("/clear-history", methods=["DELETE"])
def clear_history():
    username = request.json.get("username")
    if not username:
        return jsonify({"error": "Username required"}), 400
    clear_chat_history(username)
    return jsonify({"message": "Chat history cleared"})


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, port=5000)