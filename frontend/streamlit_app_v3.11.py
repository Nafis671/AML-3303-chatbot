import streamlit as st
import requests
import os
import time

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="SupportBot Studio",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# CUSTOM CSS
# =========================
st.markdown("""
<style>
    .block-container { padding-top: 0rem !important; padding-bottom: 1rem !important; }

    .top-bar {
        background: white;
        border-bottom: 2px solid #1a56db;
        padding: 12px 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
    }
    .top-bar-title { font-size: 1.2rem; font-weight: 700; color: #1a56db; margin: 0; }
    .top-bar-sub   { font-size: 0.72rem; color: #6b7280; margin: 0; }
    .top-bar-right { display: flex; align-items: center; gap: 10px; }
    .user-badge {
        background: #e8f0fd;
        color: #1a56db;
        border-radius: 20px;
        padding: 4px 14px;
        font-weight: 600;
        font-size: 0.82rem;
    }

    .chat-area {
        background: #f9fafb;
        border: 1px solid #d1d9e0;
        border-radius: 10px;
        padding: 16px;
        min-height: 420px;
        max-height: 420px;
        overflow-y: auto;
        margin-bottom: 10px;
    }

    .bubble-user {
        display: flex;
        justify-content: flex-end;
        align-items: flex-end;
        margin-bottom: 10px;
        gap: 8px;
    }
    .bubble-user span {
        background: #1a56db;
        color: white;
        padding: 8px 14px;
        border-radius: 16px 16px 4px 16px;
        max-width: 68%;
        font-size: 0.88rem;
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
        background: white;
        color: #1a1a2e;
        border: 1px solid #d1d9e0;
        padding: 8px 14px;
        border-radius: 16px 16px 16px 4px;
        max-width: 68%;
        font-size: 0.88rem;
        line-height: 1.5;
    }

    .avatar {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.72rem;
        font-weight: 700;
        flex-shrink: 0;
    }
    .avatar-user { background: #1a56db; color: white; }
    .avatar-bot  { background: #e8f0fd; color: #1a56db; border: 1px solid #c3d5f8; }

    .empty-chat { color: #9ca3af; font-size: 0.85rem; text-align: center; padding-top: 60px; }

    section[data-testid="stSidebar"] { background: white; border-right: 1px solid #d1d9e0; }
    .sidebar-label {
        font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.06em; color: #6b7280; margin: 12px 0 6px 0;
    }

    .doc-row {
        background: #e8f0fd; border: 1px solid #c3d5f8;
        border-radius: 6px; padding: 5px 10px;
        margin-bottom: 5px; font-size: 0.8rem;
        color: #1a1a2e; overflow: hidden;
        text-overflow: ellipsis; white-space: nowrap;
    }

    div[data-testid="stFileUploader"] > div {
        border: 1px dashed #1a56db !important;
        border-radius: 8px !important;
        background: #e8f0fd !important;
    }

    .stButton > button { border-radius: 6px !important; font-size: 0.82rem !important; }
    .stButton > button[kind="primary"] {
        background: #1a56db !important; color: white !important; border: none !important;
    }
    .stButton > button[kind="primary"]:hover { background: #1444b8 !important; }

    #MainMenu { visibility: hidden; }
    footer     { visibility: hidden; }
    header     { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# =========================
# SESSION STATE
# =========================
defaults = {
    "logged_in": False,
    "username": "",
    "chat": [],
    "loaded": False,
    "auth_mode": "Login",
    "pending_file": None,
    "pending_file_path": None,
    "uploader_key": 0,
}
for key, default in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default


# =========================
# HELPERS
# =========================
def build_bubble(role, msg, user_initial):
    if role == "user":
        return (
            '<div class="bubble-user">'
            '<span>' + msg + '</span>'
            '<div class="avatar avatar-user">' + user_initial + '</div>'
            '</div>'
        )
    return (
        '<div class="bubble-bot">'
        '<div class="avatar avatar-bot">AI</div>'
        '<span>' + msg + '</span>'
        '</div>'
    )


def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.chat = []
    st.session_state.loaded = False
    st.session_state.pending_file = None
    st.session_state.pending_file_path = None


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

        st.markdown("### " + st.session_state.auth_mode)
        username = st.text_input("Username", key="auth_username")
        password = st.text_input(
            "Password", type="password", key="auth_password")

        if st.session_state.auth_mode == "Register":
            st.caption("Username 3+ chars · Password 6+ chars · Must be unique")

        if st.button(st.session_state.auth_mode, type="primary", use_container_width=True):
            if not username or not password:
                st.error("Please fill in both fields.")
            else:
                endpoint = "register" if st.session_state.auth_mode == "Register" else "login"
                try:
                    res = requests.post(
                        "http://127.0.0.1:5000/" + endpoint,
                        json={"username": username, "password": password}
                    )
                    data = res.json()
                    if res.status_code == 200:
                        st.session_state.logged_in = True
                        st.session_state.username = data.get(
                            "username", username)
                        st.session_state.loaded = False
                        st.rerun()
                    else:
                        st.error(data.get("error", "Something went wrong."))
                except Exception as e:
                    st.error("Cannot connect to backend: " + str(e))
    st.stop()


# =========================
# LOAD CHAT HISTORY (once)
# =========================
if not st.session_state.loaded:
    try:
        res = requests.get(
            "http://127.0.0.1:5000/history",
            params={"username": st.session_state.username}
        )
        st.session_state.chat = res.json() if res.status_code == 200 else []
    except Exception:
        st.session_state.chat = []
    st.session_state.loaded = True


# =========================
# SIDEBAR
# =========================
with st.sidebar:

    st.markdown('<div class="sidebar-label">Upload Documents</div>',
                unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "drop file",
        type=["pdf", "txt", "json"],
        key="file_uploader_" + str(st.session_state.uploader_key),
        label_visibility="collapsed"
    )

    if uploaded_file is not None and st.session_state.pending_file != uploaded_file.name:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(BASE_DIR, "frontend",
                                 "data", "raw_docs", uploaded_file.name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())
        st.session_state.pending_file = uploaded_file.name
        st.session_state.pending_file_path = file_path

    if st.session_state.pending_file:
        st.caption(st.session_state.pending_file)
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
                    json={
                        "file_path": st.session_state.pending_file_path,
                        "username": st.session_state.username,
                    }
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
                st.error("Upload error: " + str(e))

    st.markdown("---")

    st.markdown('<div class="sidebar-label">Uploaded Documents</div>',
                unsafe_allow_html=True)

    try:
        docs_res = requests.get(
            "http://127.0.0.1:5000/documents",
            params={"username": st.session_state.username}
        )
        docs = docs_res.json() if docs_res.status_code == 200 else []
    except Exception:
        docs = []

    if not docs:
        st.caption("No documents yet.")
    else:
        for doc in docs:
            col_name, col_del = st.columns([5, 1])
            with col_name:
                st.markdown(
                    '<div class="doc-row">' + doc["filename"] + '</div>',
                    unsafe_allow_html=True
                )
            with col_del:
                if st.button("x", key="del_" + doc["filename"]):
                    try:
                        del_res = requests.delete(
                            "http://127.0.0.1:5000/documents/delete",
                            json={
                                "username": st.session_state.username,
                                "filename": doc["filename"],
                            }
                        )
                        if del_res.status_code == 200:
                            st.rerun()
                        else:
                            st.error("Delete failed")
                    except Exception as e:
                        st.error("Error: " + str(e))


# =========================
# MAIN AREA — TOP BAR
# =========================
user_initial = st.session_state.username[0].upper(
) if st.session_state.username else "U"

st.markdown(
    '<div class="top-bar">'
    '<div>'
    '<p class="top-bar-title">SupportBot Studio</p>'
    '<p class="top-bar-sub">AI-powered customer support assistant</p>'
    '</div>'
    '<div class="top-bar-right">'
    '<span class="user-badge">' + st.session_state.username + '</span>'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)

_, right = st.columns([8, 2])
with right:
    btn1, btn2 = st.columns(2)
    with btn1:
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()
    with btn2:
        if st.button("Clear", use_container_width=True):
            try:
                requests.delete(
                    "http://127.0.0.1:5000/clear-history",
                    json={"username": st.session_state.username}
                )
            except Exception:
                pass
            st.session_state.chat = []
            st.rerun()


# =========================
# CHAT AREA
# =========================
chat_html = "".join(
    build_bubble(role, msg, user_initial)
    for role, msg in st.session_state.chat
)

empty_placeholder = '<p class="empty-chat">No messages yet. Ask something below.</p>'

st.markdown(
    '<div class="chat-area">'
    + (chat_html if chat_html else empty_placeholder)
    + '</div>',
    unsafe_allow_html=True
)


# =========================
# CHAT INPUT ROW
# =========================
in_col, send_col = st.columns([11, 1])
with in_col:
    user_input = st.text_input(
        "",
        placeholder="Ask something about your documents...",
        key="chat_input",
        label_visibility="collapsed"
    )
with send_col:
    send = st.button("Send", type="primary", use_container_width=True)

if send and user_input.strip():
    try:
        res = requests.post(
            "http://127.0.0.1:5000/chat",
            json={"message": user_input, "username": st.session_state.username}
        )
        if res.status_code == 200:
            reply = res.json().get("response", "No response")
        else:
            reply = "Error from backend"
    except Exception as e:
        reply = "Backend error: " + str(e)

    st.session_state.chat.append(("user", user_input))
    st.session_state.chat.append(("assistant", reply))
    st.rerun()
