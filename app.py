import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from rag_pipeline import (
    answer_query,
    ingest,
    load_vector_store,
    CHROMA_PERSIST_DIR,
    DOCS_PATH,
)

st.set_page_config(page_title="Upwork API Support Bot", page_icon="🤖", layout="wide")

# Initialize states
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "history" not in st.session_state:
    st.session_state.history = []

# Auto-load logic
if st.session_state.vector_store is None and Path(CHROMA_PERSIST_DIR).exists():
    try:
        st.session_state.vector_store = load_vector_store()
    except Exception:
        pass

with st.sidebar:
    st.title("Setup")
    uploaded_file = st.file_uploader("Upload Upwork API PDF", type=["pdf"])

    if st.button("Ingest Documentation", use_container_width=True):
        if uploaded_file:
            with open("temp_docs.pdf", "wb") as f:
                f.write(uploaded_file.read())
            path = "temp_docs.pdf"
        else:
            path = DOCS_PATH

        with st.spinner("Processing..."):
            ingest(path)
            st.session_state.vector_store = load_vector_store()
            st.success("Database Ready!")

    if st.session_state.vector_store:
        st.success("✅ Vector Store Loaded")

st.title("Upwork API Technical Support Bot")

# Use a clean form for questions
with st.form("chat_form", clear_on_submit=True):
    user_query = st.text_input("Ask a technical question (e.g., 'How long is a refresh token valid?'):")
    submitted = st.form_submit_button("Ask")

if submitted and user_query:
    if not st.session_state.vector_store:
        st.error("Please ingest documentation first.")
    else:
        with st.spinner("Analyzing documentation..."):
            res = answer_query(user_query, st.session_state.vector_store)
            st.session_state.history.insert(0, {"query": user_query, **res})

# Display History
for entry in st.session_state.history:
    st.markdown(f"### ❓ {entry['query']}")
    st.markdown(f"**💡 Answer:**\n{entry['answer']}")
    with st.expander("Technical Sources (Retrieved Chunks)"):
        for i, src in enumerate(entry["sources"]):
            st.info(f"Chunk {i+1} (Page {src['metadata'].get('page','?')})")
            st.code(src["content"])
    st.divider()