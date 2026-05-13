import os
import time
from pathlib import Path
import requests

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

# --- Configuration ---
DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY", "")
DEEPINFRA_BASE_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
LLM_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"

DOCS_PATH = os.getenv("DOCS_PATH", "upwork_api_docs.pdf")
CHROMA_PERSIST_DIR = "./chroma_db"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# OPTIMIZED: Smaller chunks ensure URLs/Endpoints aren't lost in large text blocks
CHUNK_SIZE = 700
CHUNK_OVERLAP = 150
TOP_K = 10  # High Top-K to catch details scattered across different pages

SYSTEM_PROMPT = """You are a Senior Upwork API Consultant. Your mission is to provide exact technical facts.

Rules:
1. Scan the context specifically for Endpoints (URLs starting with https://), Headers (e.g., X-Upwork-...), and TTL values.
2. If the user asks for a 'URL' or 'Endpoint', provide the full string found in the text.
3. If the context contains logical technical info, use it. (e.g., if a grant is 'outside user context', it cannot see 'private user data').
4. Answer for every part of the question. If a user asks for 'grant types', list ALL types found in the context.
5. Provide reasoning (e.g., 'According to the documentation on page X...').
6. Only say 'I'm sorry' if the context has absolutely no relevance to the topic.
"""


def get_embedding_function():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)


def load_documents(pdf_path: str) -> list[Document]:
    loader = PyPDFLoader(pdf_path)
    return loader.load()


def chunk_documents(pages: list[Document]) -> list[Document]:
    # Separators prioritize keeping URLs and Headers with their descriptions
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\nStep", "\nEndpoint", "\n\n", "\n", " ", ""],
    )
    return splitter.split_documents(pages)


def build_vector_store(chunks: list[Document]) -> Chroma:
    embeddings = get_embedding_function()
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )
    return vector_store


def load_vector_store() -> Chroma:
    return Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=get_embedding_function(),
    )


def retrieve_chunks(query: str, vector_store: Chroma, top_k: int = TOP_K) -> list[Document]:
    return vector_store.similarity_search(query, k=top_k)


def call_llm(messages: list[dict]) -> tuple[str, float]:
    headers = {"Authorization": f"Bearer {DEEPINFRA_API_KEY}"}
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": 0.0,  # Zero temperature for technical accuracy
        "max_tokens": 1024,
    }

    t0 = time.time()
    # Retry logic for production stability
    for attempt in range(3):
        try:
            response = requests.post(DEEPINFRA_BASE_URL, headers=headers, json=payload, timeout=90)
            if response.status_code == 429:
                time.sleep(2 * (attempt + 1))
                continue
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip(), time.time() - t0
        except Exception as e:
            if attempt == 2: raise e
            time.sleep(1)

    return "Error", 0.0


def answer_query(query: str, vector_store: Chroma) -> dict:
    chunks = retrieve_chunks(query, vector_store)

    context_text = "\n\n---\n\n".join(
        f"[Source Page {c.metadata.get('page', '?')}]\n{c.page_content}" for c in chunks
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context From Documentation:\n{context_text}\n\nUser Question: {query}"},
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