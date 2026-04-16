import streamlit as st
import requests
import os
import time

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="AI Support Chatbot", page_icon="📚")

# st.markdown("""
#     <style>
#         /* Hide hamburger menu and footer */
#         #MainMenu {visibility: hidden;}
#         footer {visibility: hidden;}

#         /* Hide header (top bar) */
#         header {visibility: hidden;}

#         /* Optional: remove padding from top */
#         .block-container {
#             padding-top: 1rem;
#         }
#     </style>
# """, unsafe_allow_html=True)

# =========================
# SESSION STATE DEFAULTS
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "chat" not in st.session_state:
    st.session_state.chat = []
if "loaded" not in st.session_state:
    st.session_state.loaded = False
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Login"  # or "Register"


# =========================
# AUTH SCREEN
# =========================
if not st.session_state.logged_in:

    st.title("📚 AI Support Chatbot")
    st.markdown("---")

    # Toggle between Login / Register
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", use_container_width=True):
            st.session_state.auth_mode = "Login"
    with col2:
        if st.button("Register", use_container_width=True):
            st.session_state.auth_mode = "Register"

    st.markdown(f"### {st.session_state.auth_mode}")

    username = st.text_input("Username", key="auth_username")
    password = st.text_input("Password", type="password", key="auth_password")

    if st.session_state.auth_mode == "Register":
        st.caption("Username: min 3 characters · Password: min 6 characters · Username must be unique")

    submit = st.button(st.session_state.auth_mode, type="primary", use_container_width=True)

    if submit:
        if not username or not password:
            st.error("Please enter both username and password.")
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
                    st.session_state.loaded = False  # trigger history reload
                    st.rerun()
                else:
                    st.error(data.get("error", "Something went wrong."))

            except Exception as e:
                st.error(f"Could not connect to backend: {e}")

    st.stop()  # Don't render anything below if not logged in


# =========================
# LOGGED IN — HEADER
# =========================
col_title, col_user = st.columns([5, 2])
with col_title:
    st.title("📚 AI Support Chatbot")
with col_user:
    st.markdown(
        f"<div style='text-align:right; padding-top: 14px;'>👤 <b>{st.session_state.username}</b></div>",
        unsafe_allow_html=True
    )
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.chat = []
        st.session_state.loaded = False
        st.rerun()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        try:
            requests.delete(
                "http://127.0.0.1:5000/clear-history",
                json={"username": st.session_state.username}
            )
        except:
            pass
        st.session_state.chat = []
        st.rerun()


# =========================
# LOAD CHAT HISTORY (once per session)
# =========================
if not st.session_state.loaded:
    try:
        res = requests.get(
            "http://127.0.0.1:5000/history",
            params={"username": st.session_state.username}
        )
        if res.status_code == 200:
            st.session_state.chat = res.json()
        else:
            st.session_state.chat = []
    except:
        st.session_state.chat = []
    st.session_state.loaded = True


# =========================
# DISPLAY CHAT HISTORY
# =========================
for role, msg in st.session_state.chat:
    if role == "user":
        st.markdown(f"🧑 {msg}")
    else:
        st.markdown(f"🤖 {msg}")


# =========================
# SIDEBAR: DOCUMENT UPLOAD
# =========================
st.sidebar.header("📁 Upload Knowledge Documents")

uploaded_file = st.sidebar.file_uploader(
    "Upload PDF, TXT, or JSON",
    type=["pdf", "txt", "json"],
    key="file_uploader_main"
)

if uploaded_file is not None:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, "frontend", "data", "raw_docs", uploaded_file.name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    progress = st.sidebar.progress(0)
    status = st.sidebar.empty()

    try:
        status.text("📄 Reading document...")
        progress.progress(20)
        time.sleep(0.3)

        status.text("✂️ Chunking text...")
        progress.progress(40)
        time.sleep(0.3)

        status.text("🧠 Creating embeddings...")
        progress.progress(70)

        res = requests.post(
            "http://127.0.0.1:5000/upload",
            json={"file_path": file_path, "username": st.session_state.username}  # pass username
        )

        progress.progress(100)

        if res.status_code == 200:
            status.text("✅ Indexing complete!")
            st.sidebar.success("Document indexed successfully")
        else:
            status.text("❌ Indexing failed")
            st.sidebar.error(res.json().get("error", res.text))

    except Exception as e:
        st.sidebar.error(f"Upload error: {e}")

# =========================
# SIDEBAR: UPLOADED DOCUMENTS LIST
# =========================
st.sidebar.markdown("---")
st.sidebar.subheader("📄 Your Documents")

try:
    docs_res = requests.get(
        "http://127.0.0.1:5000/documents",
        params={"username": st.session_state.username}
    )
    docs = docs_res.json() if docs_res.status_code == 200 else []
except:
    docs = []

if not docs:
    st.sidebar.caption("No documents uploaded yet.")
else:
    for doc in docs:
        col_name, col_del = st.sidebar.columns([5, 1])
        with col_name:
            icon = "✅" if doc["is_embedded"] else "⏳"
            st.markdown(f"{icon} {doc['filename']}")
        with col_del:
            if st.button("✕", key=f"del_{doc['filename']}"):
                try:
                    del_res = requests.delete(
                        "http://127.0.0.1:5000/documents/delete",
                        json={"username": st.session_state.username, "filename": doc["filename"]}
                    )
                    if del_res.status_code == 200:
                        st.sidebar.success(f"Deleted {doc['filename']}")
                        st.rerun()
                    else:
                        st.sidebar.error("Delete failed")
                except Exception as e:
                    st.sidebar.error(f"Delete error: {e}")


# =========================
# CHAT INPUT
# =========================
user_input = st.chat_input("Ask something...", key="chat_input_main")

if user_input:
    st.markdown(f"🧑 {user_input}")

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
        reply = f"Backend error: {e}"

    st.markdown(f"🤖 {reply}")

    # Update local chat session
    st.session_state.chat.append(("user", user_input))
    st.session_state.chat.append(("assistant", reply))