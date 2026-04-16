import sqlite3
import hashlib

DB_PATH = "chat_history.db"


# =========================
# HELPERS
# =========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# =========================
# INIT DB (chat + users)
# =========================
def init_db():
    print("Initializing database...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Chat history table
    c.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        role TEXT,
        message TEXT
    )
    """)

    # Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Documents table
    c.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        is_embedded INTEGER DEFAULT 0,
        UNIQUE(username, filename)
    )
    """)

    conn.commit()
    conn.close()


# =========================
# DOCUMENTS: SAVE
# =========================
def save_document(username, filename, file_path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT OR REPLACE INTO documents (username, filename, file_path, is_embedded) VALUES (?, ?, ?, 0)",
            (username, filename, file_path)
        )
        conn.commit()
    finally:
        conn.close()


# =========================
# DOCUMENTS: MARK EMBEDDED
# =========================
def mark_document_embedded(username, filename):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "UPDATE documents SET is_embedded = 1 WHERE username = ? AND filename = ?",
        (username, filename)
    )
    conn.commit()
    conn.close()


# =========================
# DOCUMENTS: LIST BY USER
# =========================
def get_user_documents(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT filename, file_path, is_embedded FROM documents WHERE username = ?",
        (username,)
    )
    rows = c.fetchall()
    conn.close()
    return [{"filename": r[0], "file_path": r[1], "is_embedded": bool(r[2])} for r in rows]


# =========================
# DOCUMENTS: DELETE
# =========================
def delete_document(username, filename):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "DELETE FROM documents WHERE username = ? AND filename = ?",
        (username, filename)
    )
    conn.commit()
    conn.close()


# =========================
# USER: REGISTER
# =========================
def register_user(username, password):
    """Returns (True, 'ok') or (False, 'error reason')"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()
        return True, "registered"
    except sqlite3.IntegrityError:
        return False, "Username already taken"
    finally:
        conn.close()


# =========================
# USER: LOGIN
# =========================
def login_user(username, password):
    """Returns (True, 'ok') or (False, 'error reason')"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT password FROM users WHERE username = ?",
        (username,)
    )
    row = c.fetchone()
    conn.close()

    if row is None:
        return False, "User not found"
    if row[0] != hash_password(password):
        return False, "Incorrect password"
    return True, "ok"


# =========================
# CHAT: SAVE MESSAGE
# =========================
def save_message(username, role, message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO chats (username, role, message) VALUES (?, ?, ?)",
        (username, role, message)
    )
    conn.commit()
    conn.close()


# =========================
# CHAT: CLEAR HISTORY
# =========================
def clear_chat_history(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM chats WHERE username = ?", (username,))
    conn.commit()
    conn.close()


# =========================
# CHAT: LOAD HISTORY (by user)
# =========================
def load_chat_history(username=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if username:
        c.execute("SELECT role, message FROM chats WHERE username = ?", (username,))
    else:
        c.execute("SELECT role, message FROM chats")
    rows = c.fetchall()
    conn.close()
    return rows