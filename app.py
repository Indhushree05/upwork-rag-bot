"""
app.py
------
Part B3 – Streamlit interface for the Upwork API Support Bot.
Run with:  streamlit run app.py
"""

import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# Load .env before importing the pipeline (so env vars are available)
load_dotenv()

from rag_pipeline import (
    answer_query,
    ingest,
    load_vector_store,
    CHROMA_PERSIST_DIR,
    DOCS_PATH,
)

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Upwork API Support Bot",
    page_icon="🤖",
    layout="wide",
)

# ─────────────────────────────────────────────
# Session state – keep the vector store across reruns
# ─────────────────────────────────────────────
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

if "history" not in st.session_state:
    st.session_state.history = []  # list of {query, answer, sources, latency}

<<<<<<< HEAD
if "current_query" not in st.session_state:
    st.session_state["current_query"] = ""

=======
>>>>>>> 0906bd565adc91a0f02bbcc6b8bcdeaff6b1d93d
# FIX: Load vector store immediately on startup before any UI renders
if st.session_state.vector_store is None and Path(CHROMA_PERSIST_DIR).exists():
    try:
        st.session_state.vector_store = load_vector_store()
    except Exception as e:
<<<<<<< HEAD
=======
        # We pass here so it doesn't crash the UI if the index is corrupted
>>>>>>> 0906bd565adc91a0f02bbcc6b8bcdeaff6b1d93d
        pass

# ─────────────────────────────────────────────
# Sidebar – ingestion controls
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("Setup")
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Upload Upwork API PDF documentation",
        type=["pdf"],
        help="The PDF will be ingested locally — never sent to any external LLM.",
    )

    if st.button("Ingest / Re-ingest Documentation", use_container_width=True):
        if uploaded_file is None:
<<<<<<< HEAD
=======
            # Fall back to the path set in .env
>>>>>>> 0906bd565adc91a0f02bbcc6b8bcdeaff6b1d93d
            pdf_path = DOCS_PATH
            if not Path(pdf_path).exists():
                st.error(f"No file uploaded and '{pdf_path}' not found. "
                         "Please upload a PDF or set DOCS_PATH in .env.")
                st.stop()
        else:
<<<<<<< HEAD
=======
            # Save the uploaded bytes to a temp location
>>>>>>> 0906bd565adc91a0f02bbcc6b8bcdeaff6b1d93d
            pdf_path = "D:\\upwork_api_docs_temp.pdf"
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.read())

        with st.spinner("Ingesting documentation… this may take a minute."):
            try:
                ingest(pdf_path)
                st.session_state.vector_store = load_vector_store()
                st.success("Documentation ingested successfully!")
            except Exception as e:
                st.error(f"Ingestion failed: {e}")

    st.markdown("---")

<<<<<<< HEAD
=======
    # Status Indicator
>>>>>>> 0906bd565adc91a0f02bbcc6b8bcdeaff6b1d93d
    if st.session_state.vector_store is not None:
        st.success("✅ Vector Store Loaded")
    else:
        st.warning("⚠️ Vector Store Not Found")

    st.markdown(
        "**Model:** Meta-Llama-3.1-8B-Instruct-Turbo  \n"
        "**Embeddings:** all-MiniLM-L6-v2 (local)  \n"
        "**Vector DB:** ChromaDB"
    )

# ─────────────────────────────────────────────
# Main UI
# ─────────────────────────────────────────────
st.title("Upwork API Technical Support Bot")
st.caption(
    "Ask any question about the Upwork API. "
    "Answers are grounded exclusively in the official documentation."
)

# Evaluation questions for quick testing
st.markdown("#### Evaluation Questions")
eval_questions = [
    "What is the specific request-per-second rate limit for the Upwork API, and is it enforced per Key or per IP?",
    "How long is an OAuth access token valid for?",
    "Can I use a Client Credentials Grant to access a user's private contract details?",
]
cols = st.columns(3)
for i, (col, q) in enumerate(zip(cols, eval_questions)):
    if col.button(f"Q{i + 1}", help=q, use_container_width=True, key=f"eval_{i}"):
<<<<<<< HEAD
        st.session_state["current_query"] = q
        st.rerun()

# Query input — no key= so value= works correctly on rerun
query = st.text_input(
    "Your question:",
    value=st.session_state["current_query"],
=======
        st.session_state["prefill_query"] = q

# Query input
default_query = st.session_state.pop("prefill_query", "")
query = st.text_input(
    "Your question:",
    value=default_query,
>>>>>>> 0906bd565adc91a0f02bbcc6b8bcdeaff6b1d93d
    placeholder="e.g. How do I authenticate with OAuth 2.0?",
)

ask_button = st.button("Ask", type="primary", use_container_width=False)

if ask_button and query.strip():
<<<<<<< HEAD
    st.session_state["current_query"] = query.strip()
=======
>>>>>>> 0906bd565adc91a0f02bbcc6b8bcdeaff6b1d93d
    if st.session_state.vector_store is None:
        st.error(
            "Vector store is not loaded. "
            "Please upload the documentation and click 'Ingest' first."
        )
    else:
        with st.spinner("Thinking…"):
            try:
                result = answer_query(query.strip(), st.session_state.vector_store)
                st.session_state.history.insert(0, {"query": query.strip(), **result})
            except Exception as e:
                st.error(f"Error calling LLM: {e}")

# ─────────────────────────────────────────────
# Display results
# ─────────────────────────────────────────────
for entry in st.session_state.history:
    with st.container():
        st.markdown(f"### {entry['query']}")

<<<<<<< HEAD
        st.markdown("#### Answer")
        st.markdown(entry["answer"])

        st.caption(f"Response latency: **{entry['latency']:.2f} s**")

        with st.expander("Sources (retrieved chunks)", expanded=False):
            for i, src in enumerate(entry["sources"]):
=======
        # ── Answer ──────────────────────────────────────
        st.markdown("#### Answer")
        st.markdown(entry["answer"])

        # ── Latency ─────────────────────────────────────
        st.caption(f"Response latency: **{entry['latency']:.2f} s**")

        # ── Sources ─────────────────────────────────────
        with st.expander("Sources (retrieved chunks)", expanded=False):
            for i, src in enumerate(entry["sources"]):
                # Handle different metadata structures if necessary
>>>>>>> 0906bd565adc91a0f02bbcc6b8bcdeaff6b1d93d
                metadata = src.get("metadata", {})
                page = metadata.get("page", "?")
                st.markdown(f"**Chunk {i + 1}** — Page {page}")
                st.code(src.get("content", "No content found"), language=None)

        st.markdown("---")