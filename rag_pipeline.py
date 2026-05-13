import os
import time
from pathlib import Path
import requests

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY", "")
DEEPINFRA_BASE_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
LLM_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"

DOCS_PATH = os.getenv("DOCS_PATH", "upwork_api_docs.pdf")
CHROMA_PERSIST_DIR = "./chroma_db"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
TOP_K = 5

SYSTEM_PROMPT = """You are a Senior Upwork API Consultant with deep expertise in the Upwork developer platform. You answer developer questions strictly based on the context passages provided below. 

Rules:
1. Only use information present in the provided context.
2. If the answer is NOT in the context, respond EXACTLY with: "I'm sorry, but the provided documentation does not contain that information."
3. Never guess or fabricate details.
"""


# Helper to initialize the same embedding model everywhere
def get_embedding_function():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)


# ─────────────────────────────────────────────
# Pipeline Functions
# ─────────────────────────────────────────────

def load_documents(pdf_path: str) -> list[Document]:
    loader = PyPDFLoader(pdf_path)
    return loader.load()


def chunk_documents(pages: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.split_documents(pages)


def build_vector_store(chunks: list[Document]) -> Chroma:
    embeddings = get_embedding_function()
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )
    vector_store.persist()
    return vector_store


def load_vector_store() -> Chroma:
    embeddings = get_embedding_function()
    return Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=embeddings,
    )


def retrieve_chunks(query: str, vector_store: Chroma, top_k: int = TOP_K) -> list[Document]:
    return vector_store.similarity_search(query, k=top_k)


def call_llm(messages: list[dict]) -> tuple[str, float]:
    if not DEEPINFRA_API_KEY:
        raise EnvironmentError("DEEPINFRA_API_KEY is not set.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
    }
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 512,
    }

    t0 = time.time()

    # Retry up to 3 times on rate limit (429)
    for attempt in range(3):
        response = requests.post(DEEPINFRA_BASE_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 429:
            wait = 5 * (attempt + 1)  # 5s, 10s, 15s
            time.sleep(wait)
            continue
        break

    latency = time.time() - t0

    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip(), latency


def answer_query(query: str, vector_store: Chroma) -> dict:
    chunks = retrieve_chunks(query, vector_store)

    context_text = "\n\n---\n\n".join(
        f"[Chunk {i + 1}]\n{chunk.page_content}" for i, chunk in enumerate(chunks)
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {query}"},
    ]

    answer, latency = call_llm(messages)

    return {
        "answer": answer,
        "sources": [{"content": c.page_content, "metadata": c.metadata} for c in chunks],
        "latency": latency,
    }


def ingest(pdf_path: str = DOCS_PATH):
    pages = load_documents(pdf_path)
    chunks = chunk_documents(pages)
    build_vector_store(chunks)