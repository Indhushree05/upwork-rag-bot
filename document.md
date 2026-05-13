# Technical Summary — Upwork API RAG Support Bot

---

## Difficulties Faced

- **Chunk boundary fragmentation in code snippets.** The Upwork API docs contain long `curl` examples and JSON schemas that can be split mid-token by a naive splitter. Solved by using `RecursiveCharacterTextSplitter` with paragraph/line-break separators and a 50-character overlap so no code example loses its surrounding context entirely.

- **LLM hallucination on absent information.** Without an explicit system-level constraint, the model occasionally extrapolated beyond the retrieved chunks. Mitigated by adding a strict system prompt with a verbatim fallback response and setting `temperature=0.1` to reduce creative deviation.

- **API latency variability.** The DeepInfra endpoint can take 2–10 s depending on model load. Addressed by measuring wall-clock latency around the `requests.post` call and surfacing it prominently in the Streamlit UI so users set realistic expectations.

- **First-run embedding cost.** `sentence-transformers/all-MiniLM-L6-v2` must be downloaded (~90 MB) on the first run. Added a clear spinner and a one-time ingestion button so users are not left wondering if the app is frozen.

- **PDF text extraction quality.** `PyPDFLoader` occasionally merges lines or strips whitespace in multi-column layouts. A sanity-check print of character count and a 400-character sample was added to the ingestion step so any extraction anomaly is immediately visible during setup.

---

## How LLMs Were Used During Development

Claude (Anthropic) was used as a coding assistant throughout the project:
- Drafted the initial `rag_pipeline.py` structure and suggested `RecursiveCharacterTextSplitter` over `CharacterTextSplitter` for better code-snippet handling.
- Helped refine the system prompt wording to balance staying in character with correctly triggering the hallucination-guard fallback.
- Reviewed the Streamlit layout and suggested the session-state pattern for keeping the vector store across reruns without re-loading on every interaction.

All generated code was reviewed, understood, and in several cases rewritten before inclusion. No documentation was uploaded to any external LLM.

---

## 3 Reasons I Am the Best Candidate for the ProAnalyst AI Team

1. **RAG architecture ownership end-to-end.** I understand every layer of this stack — from PDF extraction and chunk-overlap rationale to embedding similarity search and prompt engineering — not just how to wire libraries together.

2. **Hallucination-aware engineering mindset.** I treat grounding and non-fabrication as first-class requirements, not afterthoughts. The system prompt and temperature choices in this submission reflect that instinct, which is critical for a product that surfaces API documentation to developers.

3. **Production-ready habits.** Environment-variable secrets, a `.env.example`, a one-time ingestion step that persists the index, clear error messages, and latency telemetry in the UI — these are the details that separate a demo from a deployable tool, and they are habits I bring to every project.