# 🤖 AI-Powered Support Chatbot (RAG Document Retrieval System)

A Retrieval-Augmented Generation (RAG) based AI chatbot that allows users to ask questions over documents (PDFs, text files, etc.) using embeddings, FAISS vector search, and OpenAI LLM responses.

---

## 🚀 Project Features

- 📄 PDF document ingestion and processing
- 🔍 FAISS vector similarity search
- 🧠 OpenAI LLM integration for intelligent responses
- ⚡ Flask backend API
- 💬 Streamlit frontend chat UI
- 📚 Chat history tracking
- 🧩 RAG (Retrieval Augmented Generation) pipeline

---

## 🧰 Tech Stack

- Python
- Flask
- Streamlit
- OpenAI API
- FAISS (vector database)
- PyPDF
- NumPy
- Tiktoken
- Python-dotenv

---

## ⚙️ Project Setup Guide

---

## 1. Clone the Repository
```bash
git clone <your-repo-url>
cd ai-support-rag-chatbot

## 2. Create the virtual environment

python -m venv venv
## 3.activate virtual environment
venv\Scripts\activate

## 4. Install Dependencies
pip install flask streamlit openai python-dotenv faiss-cpu pypdf numpy tiktoken requests

##Setup Environment Variables
OPENAI_API_KEY=your_api_key_here

## 5. Initialize Database
cd backend
python
## then run 
from db import init_db
init_db()
exit()

## 6. Run Backend Server (Flask)
python app.py

## check the backend server on
 http://127.0.0.1:5000

## 7. Run Frontend (Streamlit UI)
```bash
cd frontend
streamlit run streamlit_app.py

## 8.Test Backend API
http://127.0.0.1:5000/history

#expected output
[]

## 9. test documents 
 test the documents accordingly
