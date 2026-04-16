import streamlit as st
import requests
import os
import time

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="SupportBot Studio",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# CUSTOM CSS
# =========================
st.markdown("""
<style>
    /* ── Hide Streamlit chrome ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ══════════════════════════════════════
       PALETTE
       --blue-dark  : #1e40af   (header, user bubble)
       --blue-mid   : #3b82f6   (accents, borders)
       --blue-light : #dbeafe   (sidebar, bot bubble bg)
       --blue-pale  : #eff6ff   (main bg, chat bg)
       --white      : #ffffff
       --text-dark  : #1e3a5f
       --text-mid   : #3b5ea6
       --text-muted : #6b90c4
    ══════════════════════════════════════ */

    /* ── Global white background ── */
    html, body,
    [data-testid="stApp"],
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > section,
    .main, .main > div,
    [data-testid="stVerticalBlock"] {
        background-color: #eff6ff !important;
        color: #1e3a5f !important;
    }

    /* No outer page scroll */
    html, body { overflow: hidden !important; height: 100% !important; }

    .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
        height: 100vh !important;
        overflow: hidden !important;
    }

    [data-testid="stVerticalBlock"] > div { gap: 0 !important; }
    div[data-testid="column"] { padding: 0 2px !important; }

    /* ── Top bar ── */
    .top-bar {
        background: #1e40af;
        padding: 10px 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 4px;
    }
    .top-bar-title { font-size: 1.05rem; font-weight: 700; color: #ffffff; margin: 0; }
    .top-bar-sub   { font-size: 0.68rem; color: #bfdbfe; margin: 0; }
    .user-badge {
        background: #2563eb;
        color: #ffffff;
        border-radius: 20px;
        padding: 3px 12px;
        font-weight: 600;
        font-size: 0.80rem;
        border: 1px solid #93c5fd;
    }

    /* ── Chat area ── */
    .chat-area {
        background: #ffffff;
        border: 1px solid #bfdbfe;
        border-radius: 10px;
        padding: 14px 16px;
        height: calc(100vh - 225px);
        overflow-y: auto;
        margin-bottom: 6px;
    }

    /* ── Chat bubbles ── */
    .bubble-user {
        display: flex;
        justify-content: flex-end;
        align-items: flex-end;
        margin-bottom: 10px;
        gap: 8px;
    }
    .bubble-user span {
        background: #1e40af;
        color: #ffffff;
        padding: 8px 13px;
        border-radius: 14px 14px 3px 14px;
        max-width: 68%;
        font-size: 0.87rem;
        line-height: 1.5;
    }
    .bubble-bot {
        display: flex;
        justify-content: flex-start;
        align-items: flex-end;
        margin-bottom: 10px;
        gap: 8px;
    }
    .bubble-bot span {
        background: #dbeafe;
        color: #1e3a5f;
        border: 1px solid #bfdbfe;
        padding: 8px 13px;
        border-radius: 14px 14px 14px 3px;
        max-width: 68%;
        font-size: 0.87rem;
        line-height: 1.5;
    }

    /* ── Avatars ── */
    .avatar {
        width: 28px; height: 28px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.68rem; font-weight: 700; flex-shrink: 0;
    }
    .avatar-user { background: #1e40af; color: #ffffff; }
    .avatar-bot  { background: #bfdbfe; color: #1e40af; }

    .empty-chat { color: #93c5fd; font-size: 0.85rem; text-align: center; padding-top: 80px; }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] > div > div,
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        background: #dbeafe !important;
        border-right: 1px solid #93c5fd;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] label { color: #1e40af !important; }
    .sidebar-label {
        font-size: 0.70rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.06em;
        color: #3b82f6 !important; margin: 12px 0 5px 0;
    }

    /* ── Doc row ── */
    .doc-row {
        background: #eff6ff; border: 1px solid #93c5fd; border-radius: 5px;
        padding: 4px 9px; margin-bottom: 4px;
        font-size: 0.78rem; color: #1e3a5f;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }

    /* ── File uploader ── */
    div[data-testid="stFileUploader"],
    div[data-testid="stFileUploader"] > div,
    div[data-testid="stFileUploader"] > div > div,
    div[data-testid="stFileUploader"] section,
    div[data-testid="stFileUploader"] label {
        background: #eff6ff !important;
        color: #1e40af !important;
    }
    div[data-testid="stFileUploader"] > div {
        border: 1px dashed #3b82f6 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stFileUploader"] button {
        background: #dbeafe !important;
        color: #1e40af !important;
        border: 1px solid #3b82f6 !important;
    }
    div[data-testid="stFileUploader"] small,
    div[data-testid="stFileUploader"] span,
    div[data-testid="stFileUploader"] p { color: #3b82f6 !important; }

    /* ── Buttons ── */
    .stButton > button {
        border-radius: 6px !important;
        font-size: 0.82rem !important;
        transition: background 0.15s ease !important;
    }
    .stButton > button[kind="primary"] {
        background: #1e40af !important; color: #ffffff !important; border: none !important;
    }
    .stButton > button[kind="primary"]:hover { background: #1d4ed8 !important; }
    .stButton > button[kind="secondary"] {
        background: #dbeafe !important; color: #1e40af !important; border: 1px solid #93c5fd !important;
    }
    .stButton > button[kind="secondary"]:hover { background: #bfdbfe !important; }

    /* Logout button */
    div[data-testid="stSidebar"] .logout-area button {
        background: #eff6ff !important;
        color: #1e40af !important;
        border: 1px solid #93c5fd !important;
    }
    div[data-testid="stSidebar"] .logout-area button:hover {
        background: #dbeafe !important;
    }

    /* ── Text input ── */
    .stTextInput input {
        background: #ffffff !important;
        border: 1px solid #93c5fd !important;
        color: #1e3a5f !important;
        border-radius: 8px !important;
    }
    .stTextInput input::placeholder { color: #93c5fd !important; }
    .stTextInput input:focus {
        border-color: #1e40af !important;
        box-shadow: 0 0 0 2px rgba(30,64,175,0.12) !important;
    }

    /* Keep the input row always visible at bottom */
    div[data-testid="stHorizontalBlock"]:last-child {
        position: sticky;
        bottom: 0;
        background: #eff6ff;
        padding: 6px 0 4px 0;
        z-index: 100;
    }
</style>
""", unsafe_allow_html=True)


# =========================
# SESSION STATE
# =========================
for key, default in [
    ("logged_in", False), ("username", ""), ("chat", []),
    ("loaded", False), ("auth_mode", "Login"),
    ("pending_file", None), ("pending_file_path", None),
    ("uploader_key", 0)
]:
    if key not in st.session_state:
        st.session_state[key] = default


# =========================
# AUTH SCREEN
# =========================
if not st.session_state.logged_in:
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("## SupportBot Studio")
        st.markdown("---")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Login", use_container_width=True):
                st.session_state.auth_mode = "Login"
        with c2:
            if st.button("Register", use_container_width=True):
                st.session_state.auth_mode = "Register"

        st.markdown(f"### {st.session_state.auth_mode}")
        username = st.text_input("Username", key="auth_username")
        password = st.text_input("Password", type="password", key="auth_password")

        if st.session_state.auth_mode == "Register":
            st.caption("Username 3+ chars · Password 6+ chars · Must be unique")

        if st.button(st.session_state.auth_mode, type="primary", use_container_width=True):
            if not username or not password:
                st.error("Please fill in both fields.")
            else:
                endpoint = "register" if st.session_state.auth_mode == "Register" else "login"
                try:
                    res = requests.post(
                        f"http://127.0.0.1:5000/{endpoint}",
                        json={"username": username, "password": password}
                    )
                    data = res.json()
                    if res.status_code == 200:
                        st.session_state.logged_in = True
                        st.session_state.username = data.get("username", username)
                        st.session_state.loaded = False
                        st.rerun()
                    else:
                        st.error(data.get("error", "Something went wrong."))
                except Exception as e:
                    st.error(f"Cannot connect to backend: {e}")
    st.stop()


# =========================
# LOAD CHAT HISTORY (once)
# =========================
if not st.session_state.loaded:
    try:
        res = requests.get("http://127.0.0.1:5000/history",
                           params={"username": st.session_state.username})
        st.session_state.chat = res.json() if res.status_code == 200 else []
    except:
        st.session_state.chat = []
    st.session_state.loaded = True


# =========================
# SIDEBAR
# =========================
with st.sidebar:

    # ---- Upload section ----
    st.markdown('<div class="sidebar-label">Upload Documents</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "drop file", type=["pdf", "txt", "json"],
        key=f"file_uploader_{st.session_state.uploader_key}",
        label_visibility="collapsed"
    )

    # Stage file on selection
    if uploaded_file is not None and st.session_state.pending_file != uploaded_file.name:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(BASE_DIR, "frontend", "data", "raw_docs", uploaded_file.name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())
        st.session_state.pending_file = uploaded_file.name
        st.session_state.pending_file_path = file_path

    # Confirm upload button
    if st.session_state.pending_file:
        st.caption(f"{st.session_state.pending_file}")
        if st.button("Upload", type="primary", use_container_width=True):
            prog = st.progress(0)
            stat = st.empty()
            try:
                stat.text("Reading...")
                prog.progress(25)
                time.sleep(0.2)
                stat.text("Chunking...")
                prog.progress(55)
                time.sleep(0.2)
                stat.text("Embedding...")
                prog.progress(80)

                res = requests.post(
                    "http://127.0.0.1:5000/upload",
                    json={"file_path": st.session_state.pending_file_path,
                          "username": st.session_state.username}
                )
                prog.progress(100)

                if res.status_code == 200:
                    stat.text("Done!")
                    st.session_state.pending_file = None
                    st.session_state.pending_file_path = None
                    st.session_state.uploader_key += 1
                    time.sleep(0.6)
                    st.rerun()
                else:
                    stat.text("Failed")
                    st.error(res.json().get("error", res.text))
            except Exception as e:
                st.error(f"Upload error: {e}")

    st.markdown("---")

    # ---- Uploaded docs list ----
    st.markdown('<div class="sidebar-label">Uploaded Documents</div>', unsafe_allow_html=True)

    try:
        docs_res = requests.get("http://127.0.0.1:5000/documents",
                                params={"username": st.session_state.username})
        docs = docs_res.json() if docs_res.status_code == 200 else []
    except:
        docs = []

    if not docs:
        st.caption("No documents yet.")
    else:
        for doc in docs:
            col_name, col_del = st.columns([5, 1])
            with col_name:
                st.markdown(f'<div class="doc-row">{doc["filename"]}</div>',
                            unsafe_allow_html=True)
            with col_del:
                if st.button("x", key=f"del_{doc['filename']}"):
                    try:
                        del_res = requests.delete(
                            "http://127.0.0.1:5000/documents/delete",
                            json={"username": st.session_state.username,
                                  "filename": doc["filename"]}
                        )
                        if del_res.status_code == 200:
                            st.rerun()
                        else:
                            st.error("Delete failed")
                    except Exception as e:
                        st.error(f"Error: {e}")

    # ---- Logout pinned to sidebar bottom ----
    st.markdown("<br>" * 4, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<div class="logout-area">', unsafe_allow_html=True)
    if st.button("Logout", use_container_width=True, key="logout_btn"):
        for key in ["logged_in", "username", "chat", "loaded",
                    "pending_file", "pending_file_path"]:
            st.session_state[key] = False if key == "logged_in" else (
                [] if key == "chat" else (False if key == "loaded" else None if "file" in key else "")
            )
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# =========================
# MAIN AREA — TOP BAR
# =========================
user_initial = st.session_state.username[0].upper() if st.session_state.username else "U"

st.markdown(f"""
<div class="top-bar">
    <div>
        <p class="top-bar-title">SupportBot Studio</p>
        <p class="top-bar-sub">AI-powered customer support assistant</p>
    </div>
    <span class="user-badge">{st.session_state.username}</span>
</div>
""", unsafe_allow_html=True)

# Clear history — compact top-right
_, right = st.columns([10, 2])
with right:
    if st.button("Clear history", use_container_width=True):
        try:
            requests.delete("http://127.0.0.1:5000/clear-history",
                            json={"username": st.session_state.username})
        except:
            pass
        st.session_state.chat = []
        st.rerun()


# =========================
# CHAT AREA
# =========================
def build_bubble(role, msg, user_initial):
    if role == "user":
        return (
            f'<div class="bubble-user">'
            f'<span>{msg}</span>'
            f'<div class="avatar avatar-user">{user_initial}</div>'
            f'</div>'
        )
    else:
        return (
            f'<div class="bubble-bot">'
            f'<div class="avatar avatar-bot">AI</div>'
            f'<span>{msg}</span>'
            f'</div>'
        )

chat_html = "".join(
    build_bubble(role, msg, user_initial)
    for role, msg in st.session_state.chat
)

st.markdown(
    f'<div class="chat-area">'
    f'{chat_html if chat_html else "<p class=\'empty-chat\'>No messages yet. Ask something below.</p>"}'
    f'</div>',
    unsafe_allow_html=True
)


# =========================
# CHAT INPUT ROW (full width)
# =========================
in_col, send_col = st.columns([11, 1])
with in_col:
    user_input = st.text_input(
        "", placeholder="Ask something about your documents...",
        key="chat_input", label_visibility="collapsed"
    )
with send_col:
    send = st.button("Send", type="primary", use_container_width=True)

if send and user_input.strip():
    try:
        res = requests.post(
            "http://127.0.0.1:5000/chat",
            json={"message": user_input, "username": st.session_state.username}
        )
        reply = res.json().get("response", "No response") if res.status_code == 200 else "Error from backend"
    except Exception as e:
        reply = f"Backend error: {e}"

    st.session_state.chat.append(("user", user_input))
    st.session_state.chat.append(("assistant", reply))
    st.rerun()