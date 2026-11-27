# Advanced RAG Concepts — Learning Roadmap

Hands-on path from RAG fundamentals to production-grade retrieval systems, learned by building real projects with a proper backend (FastAPI) and a nominal frontend (React).

**Cadence:** 3 sessions/week × 3–4 hrs (~10 hrs/week). Each milestone ≈ 1 week.

---

## Guiding principles

1. **Build it by hand first, then use frameworks.** Project 1 is framework-light so every step of the pipeline is understood. Project 2 rebuilds with a framework to compare.
2. **Measure everything.** Evaluation lands in M4 — every later technique is judged against a baseline, not by feel.
3. **Engineering standards from day one.** Typed, tested, linted, configured, logged — treated as part of the learning, not cleanup.
4. **Providers are swappable.** LLM, embedder and reranker sit behind interfaces; switching provider is a config change.
5. **$0 budget.** Everything runs locally or on free tiers.

---

## Tech stack

| Layer | Choice | Cost |
|---|---|---|
| Backend | Python, FastAPI, Pydantic | Free |
| Frontend | React (Vite) — nominal UI | Free |
| LLM | **Ollama** (local, Docker, CPU) for development + **Google Gemini API** (free tier) for quality/eval — swappable behind `LLMClient` | Free |
| Embeddings | Local BGE via sentence-transformers, Ollama embedding models (e.g. `nomic-embed-text`) → Voyage AI (free tier) for comparison | Free |
| Vector store | Postgres + pgvector (Docker) | Free |
| Keyword search | Postgres full-text search (BM25-style) | Free |
| Reranker | Local cross-encoder (bge-reranker) → Voyage rerank for comparison | Free |
| Tracing / observability | Lightweight option chosen in M4 — Arize Phoenix (single container) or Langfuse Cloud free tier | Free |
| Infra | Docker Compose (Postgres + Ollama) | Free |

### Where each LLM is used

| Job | Provider | Why |
|---|---|---|
| Learning Docker & local model serving | Ollama | Hands-on with containers, volumes, model pulls |
| Day-to-day development (M1–M3) | Ollama, small (~3B) model | Offline, no API key, no rate limits, data stays local |
| Answer quality & evaluation runs (M4+) | Gemini | Much stronger; CPU inference is too slow for full eval runs |
| LLM-as-judge | Gemini | Small local models are unreliable judges |
| Experiment (M4) | Ollama vs Gemini on the same eval set | Measure quality / latency / cost trade-offs |

### Machine constraints (dev box)

- **CPU-only inference:** Intel i5-7500 (4 cores), integrated GPU — Ollama cannot use GPU acceleration. Expect ~5–10 tokens/s on 3B models and long prompt-processing times on RAG-sized prompts.
- **RAM:** 16 GB total, ~7.7 GB allocated to Docker (raise via `.wslconfig` if needed).
- **Disk:** Docker data stored on **D:** (more free space than C:).
- **Windows Application Control** blocks venv `.exe` launchers → always run tools as `uv run python -m <tool>`.

> **Note:** Gemini's free tier may use prompts to improve Google's products — use public documents only.
> Free-tier limits change often; check provider consoles for current numbers.
> Self-hosted Langfuse needs ~4 extra containers (Postgres, ClickHouse, Redis, MinIO) — too heavy alongside Ollama on this machine.

---

## Engineering standards (applied in every milestone)

- [ ] **Dependencies:** `uv` with a lockfile
- [ ] **Quality:** `ruff` (lint + format), `mypy` (type check), `pre-commit` hooks
- [ ] **Testing:** `pytest` — unit tests (chunkers, parsers), integration tests against real Postgres (testcontainers)
- [ ] **CI:** GitHub Actions — lint, type check, tests, small eval regression subset
- [ ] **Architecture:** layered — `api/` → `services/` → `repositories/` + `providers/`; dependencies wired via FastAPI `Depends`
- [ ] **Contracts:** Pydantic models for every request/response
- [ ] **Config:** `pydantic-settings`; `.env.example` committed, `.env` never committed
- [ ] **Database:** Alembic migrations — no hand-edited schemas
- [ ] **Logging:** structured logs with request IDs
- [ ] **Decisions:** short ADRs in `docs/adr/` for each meaningful choice (why pgvector, why this chunk size, …)
- [ ] **Git:** small commits, conventional commit messages

---

## Test corpus (15–25 public PDFs)

Chosen so each document type stresses a different failure mode.

| PDF type | Source | Tests |
|---|---|---|
| Research papers | arXiv | Two-column layout, equations, references |
| Government publications | NIST Special Publications, IRS publications | Long docs, deep section hierarchy, tables |
| Product manuals | Manufacturers' public manuals | Step lists, warnings, image-heavy pages |
| Annual reports | Company investor-relations pages | Financial tables, exact numeric answers |
| Scanned documents | Internet Archive | No text layer → OCR |
| Slide decks (PDF) | Conference talks | Sparse text, bullet fragments |

Stored under `data/corpus/` (git-ignored), with a `data/corpus/MANIFEST.md` listing source URLs.

---

# Project 1 — PDF Knowledge Assistant (main build)

Upload a varied collection of PDFs, ask questions in a chat UI, and get streamed answers with page-level citations — backed by an ingestion pipeline, evaluation suite and production-style API.

**Covers:** Levels 0–4 (foundations → core pipeline → retrieval quality → evaluation → production).

---

### M0 — Project setup & standards

**Goal:** A clean, runnable skeleton that enforces the engineering standards.

- [ ] `git init`, `.gitignore`, README
- [ ] Repo layout: `backend/`, `frontend/`, `experiments/`, `data/`, `docs/adr/`
- [ ] Backend: FastAPI app, `uv`, `ruff`, `mypy`, `pytest`, `pre-commit`
- [ ] Settings via `pydantic-settings` + `.env.example`
- [ ] Structured logging, `/health` endpoint
- [ ] Docker Desktop: move disk image to D:, check memory allocation
- [ ] Docker Compose: Postgres + pgvector
- [ ] Docker Compose: Ollama service (pinned version, models in a volume)
- [ ] Pull a small chat model (~3B) + an embedding model; measure tokens/s on this machine
- [ ] Alembic initialised, first migration (enable `vector` extension)
- [ ] Frontend: React (Vite) skeleton calling `/health`
- [ ] GitHub Actions CI: lint, type check, tests
- [ ] ADR-001: stack choice

**Done when:** `docker compose up` (Postgres + Ollama) + backend + frontend run; Ollama answers a prompt; CI is green; one passing test.

---

### M1 — RAG from scratch (Level 0)

**Goal:** Understand what every framework hides. No framework, no database — scripts in `experiments/`.

- [ ] Extract text from 2–3 PDFs (`pypdf` / PyMuPDF)
- [ ] Naive fixed-size chunking
- [ ] Embeddings with `all-MiniLM-L6-v2` and `bge-small-en-v1.5`; cosine similarity in numpy
- [ ] Top-k retrieval → prompt → **Ollama** (local) → answer — no API key needed
- [ ] **Retrieval comparison experiment** on the same 10 questions:
  - [ ] Bag-of-words / TF-IDF
  - [ ] BM25
  - [ ] Averaged word2vec
  - [ ] MiniLM
  - [ ] BGE
  - [ ] Ollama embedding model (e.g. `nomic-embed-text`)
- [ ] Write up findings in `experiments/m1_findings.md` (why word2vec fails, where BM25 still wins)

**Learn:** embeddings, similarity, sparse vs dense retrieval, the minimal RAG loop.
**Done when:** a ~100-line script answers questions over your PDFs, and you can explain the comparison results.

---

### M2 — Ingestion pipeline (Level 1)

**Goal:** Turn the script into a real ingestion service.

- [ ] Data model: `documents`, `chunks` (text, embedding, page number, section, metadata)
- [ ] `POST /documents` upload endpoint; file storage
- [ ] Background processing (FastAPI `BackgroundTasks` first) with document status (`pending → processing → ready / failed`)
- [ ] PDF parsing with page tracking
- [ ] Three chunking strategies behind one interface:
  - [ ] Fixed-size with overlap
  - [ ] Recursive (paragraph → sentence)
  - [ ] Structure-aware (headings/sections)
- [ ] `Embedder` interface; implementations: local BGE (sentence-transformers) + Ollama; batched embedding
- [ ] Store vectors in pgvector; HNSW index
- [ ] `GET /documents`, `GET /documents/{id}`, `DELETE /documents/{id}` (deletes chunks too)
- [ ] Unit tests for chunkers; integration test for ingestion
- [ ] ADR: chunking strategy and chunk size defaults

**Learn:** parsing, chunking trade-offs, embedding batching, vector indexing (HNSW vs IVF).
**Done when:** uploading a PDF produces searchable, page-tagged chunks in pgvector.

---

### M3 — Query & chat (Level 1)

**Goal:** End-to-end question answering with citations.

- [ ] `LLMClient` interface with **two** implementations: `OllamaClient` and `GeminiClient` (both streaming); provider chosen in config
- [ ] Retrieval service (vector search, top-k, metadata filters by document)
- [ ] Prompt templates kept in files, versioned
- [ ] Grounded answers with **citations** (document + page)
- [ ] "I don't know" behaviour when context is insufficient
- [ ] `POST /chat` with **streaming via SSE**
- [ ] Retry with backoff + handling for free-tier rate limits
- [ ] Frontend: document upload, chat box, streamed answer, clickable source list

**Learn:** prompt construction, grounding, citations, streaming, handling rate limits.
**Done when:** you can ask a question in the UI and get a streamed, cited answer.

---

### M4 — Evaluation & observability (Level 3)

**Goal:** Turn "it seems better" into numbers. Every later milestone is measured against this baseline.

- [ ] Golden dataset: 40–50 questions spread across PDF types, each with expected source chunk(s)/page(s) and a reference answer
- [ ] Retrieval metrics: recall@k, MRR, nDCG
- [ ] Generation metrics: faithfulness, answer relevance (LLM-as-judge; optionally RAGAS)
- [ ] Eval runner CLI: `uv run eval --config <pipeline-config>` → results saved as JSON + markdown report
- [ ] Results broken down **by PDF type**
- [ ] LLM-as-judge runs on Gemini
- [ ] **Ollama vs Gemini comparison** on the same eval set: quality, latency, tokens/s → `docs/eval/llm_comparison.md`
- [ ] Choose tracing tool (Phoenix vs Langfuse Cloud) — ADR; trace every request (retrieval, prompt, LLM call, latency, tokens)
- [ ] Small eval subset added to CI as a regression gate
- [ ] **Baseline report** committed to `docs/eval/baseline.md`

**Learn:** retrieval vs generation metrics, LLM-as-judge pitfalls, tracing, regression testing for RAG.
**Done when:** one command produces a scored report, and the baseline is recorded.

---

### M5 — Retrieval quality (Level 2)

**Goal:** Improve retrieval, proving each change with the eval suite.

- [ ] **Hybrid search:** Postgres full-text + vector, merged with Reciprocal Rank Fusion
- [ ] **Reranking:** retrieve top 50 → rerank → top 5
  - [ ] Local cross-encoder (`bge-reranker-base` / `ms-marco-MiniLM`)
  - [ ] Voyage rerank (free tier) — compare
- [ ] **Query transformation:** rewriting, multi-query, HyDE
- [ ] **Parent-document / small-to-big** retrieval
- [ ] **MMR** for result diversity
- [ ] Swap embeddings: local BGE vs Voyage (requires re-indexing — note the lesson)
- [ ] Comparison table of every technique vs baseline in `docs/eval/m5_results.md`

**Learn:** bi-encoder vs cross-encoder, sparse + dense fusion, query-side vs index-side improvements, cost/latency trade-offs.
**Done when:** each technique has a measured before/after; best config becomes the default.

---

### M6 — Hard PDFs

**Goal:** Handle the document types that break naive parsing.

- [ ] Identify worst-scoring PDF types from the M4/M5 per-type breakdown
- [ ] Tables: table-aware extraction (e.g., pdfplumber / layout-aware parsers), tables kept intact as chunks
- [ ] Multi-column layouts: correct reading order
- [ ] Scanned PDFs: OCR (Tesseract) with detection of missing text layer
- [ ] Parser selection per document (route by detected type)
- [ ] Re-run evals; per-type before/after in `docs/eval/m6_results.md`

**Learn:** why ingestion quality caps retrieval quality; layout-aware parsing; OCR trade-offs.
**Done when:** table and scanned-document questions show a measured improvement.

---

### M7 — Conversational RAG (Level 4)

**Goal:** Multi-turn chat that understands follow-ups.

- [ ] Conversation + message persistence (Postgres)
- [ ] Query condensation: rewrite follow-ups into standalone questions using chat history
- [ ] History window / summarisation to control tokens
- [ ] Frontend: conversation list, resume previous chats
- [ ] Add multi-turn cases to the golden dataset

**Learn:** conversational retrieval, memory strategies, token budgeting.
**Done when:** "What about the second one?" retrieves the right context.

---

### M8 — Production concerns (Level 4)

**Goal:** Make it behave like a real service.

- [ ] Authentication (JWT)
- [ ] Multi-tenancy: documents owned by users/teams; **access control enforced at retrieval time**
- [ ] Caching: exact-match response cache; embedding cache
- [ ] Prompt-injection defence for retrieved content; input/output guardrails
- [ ] API rate limiting; request timeouts
- [ ] Background worker upgrade (e.g., arq / Celery) for ingestion
- [ ] Containerise backend + frontend; full `docker compose up` deployment
- [ ] Cost & latency dashboard from tracing data

**Learn:** security, isolation, performance, operating a RAG service.
**Done when:** two users can't see each other's documents, and the full stack runs from one command.

---

# Project 2 — Framework rebuild & comparison (~3–4 weeks)

**Idea:** Support assistant over product manuals + FAQs, built **with LlamaIndex or LangChain**.

- [ ] Rebuild ingestion + retrieval + chat using the framework
- [ ] Reuse the M4 eval approach; compare quality, code size, flexibility vs Project 1
- [ ] Incremental re-sync of changed documents (hashing, upserts, deletions)
- [ ] Semantic cache
- [ ] User feedback (👍/👎) feeding back into the eval dataset
- [ ] Write-up: what the framework gave, hid, and got in the way of

---

# Project 3 — Advanced patterns (optional, later)

To be scoped once Projects 1–2 are complete. Candidates: agentic RAG (routing, self-correction), GraphRAG, text-to-SQL alongside documents, multimodal retrieval.

---

## Progress log

| Date | Milestone | Notes |
|---|---|---|
| 2026-11-27 | — | Roadmap created |
| 2026-11-27 | M0 | Backend scaffolded (uv, ruff, mypy, pytest). Added Ollama (local, CPU) alongside Gemini — hybrid LLM plan; tracing tool decision moved to M4 |
