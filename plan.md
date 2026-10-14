# CodeLens AI — Implementation Plan

> A multi-agent AI code review system powered by RAG, LangGraph, and Azure OpenAI GPT-4o.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Folder Structure](#folder-structure)
- [Storage Strategy](#storage-strategy)
- [Step 1 — Project Scaffolding](#step-1--project-scaffolding)
- [Step 2 — Azure OpenAI Connection](#step-2--azure-openai-connection)
- [Step 3 — Knowledge Base Collection](#step-3--knowledge-base-collection)
- [Step 4 — Chunking and Local Vector Store](#step-4--chunking-and-local-vector-store)
- [Step 5 — RAG Retriever](#step-5--rag-retriever)
- [Step 6 — Pydantic Schemas](#step-6--pydantic-schemas)
- [Step 7 — Individual Agents](#step-7--individual-agents)
- [Step 8 — LangGraph Orchestration](#step-8--langgraph-orchestration)
- [Step 9 — Local Session Storage](#step-9--local-session-storage)
- [Step 10 — Follow-Up Conversation Support](#step-10--follow-up-conversation-support)
- [Step 11 — FastAPI Endpoints](#step-11--fastapi-endpoints)
- [Step 12 — Streaming Responses](#step-12--streaming-responses)
- [Step 13 — GitHub URL Support](#step-13--github-url-support)
- [Step 14 — Logging and Observability](#step-14--logging-and-observability)
- [Step 15 — Evaluation Benchmark](#step-15--evaluation-benchmark)
- [Step 16 — Database Migration](#step-16--database-migration)
- [Step 17 — README and Portfolio Polish](#step-17--readme-and-portfolio-polish)
- [Environment Variables](#environment-variables)

---

## Project Overview

### The Problem

Code reviews are slow, inconsistent, and limited by individual reviewer expertise. Linters catch syntax issues but miss contextual problems like architectural violations, security vulnerabilities hidden in business logic, or performance antipatterns that only surface at scale.

### The Solution

CodeLens AI acts as a virtual review team — three specialist agents (Security, Architecture, Performance) analyze code in parallel, each backed by a curated knowledge base via RAG. A synthesizer merges their findings into one prioritized, structured review. Users can then have a conversation about the findings, ask for explanations, or submit corrected code for re-review.

### Why This Project Stands Out

- Solves a problem every engineering interviewer personally faces
- Demonstrates RAG, multi-agent orchestration, structured outputs, and stateful conversations in one coherent system
- Not a chatbot or document Q&A — it is a differentiated, practical tool
- Demo-friendly: paste code, get a review, have a conversation — value is visible in 60 seconds

---

## Tech Stack

| Layer                | Tool                                | Why                                                                      |
| -------------------- | ----------------------------------- | ------------------------------------------------------------------------ |
| API Framework        | FastAPI (async)                     | Industry standard for async Python APIs                                  |
| Agent Orchestration  | LangGraph                           | Graph-based state machine, supports parallel execution and checkpointing |
| LLM                  | Azure OpenAI GPT-4o                 | Enterprise-grade, your existing Azure setup                              |
| Embeddings           | Azure OpenAI text-embedding-ada-002 | Consistent provider, 1536-dim vectors                                    |
| Vector Store (local) | FAISS                               | Zero-infra local development                                             |
| Vector Store (prod)  | PostgreSQL + pgvector               | Single database for everything                                           |
| Relational DB        | PostgreSQL                          | Sessions, reviews, findings, chat history                                |
| ORM                  | Async SQLAlchemy                    | Async-native, production-grade                                           |
| Migrations           | Alembic                             | Industry standard for SQLAlchemy                                         |
| Containerization     | Docker Compose                      | One-command startup                                                      |

---

## Folder Structure

```
codelens-ai/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
├── .gitignore
├── README.md
├── alembic/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── media/
│   ├── knowledge_base/
│   │   ├── security/
│   │   ├── architecture/
│   │   └── performance/
│   ├── vector_store/
│   ├── sessions/
│   │   └── {session_id}/
│   │       ├── session.json
│   │       ├── review.json
│   │       ├── findings.json
│   │       └── chat_history.json
│   └── logs/
├── scripts/
│   ├── test_llm.py
│   ├── ingest_knowledge.py
│   ├── test_security_agent.py
│   ├── test_architecture_agent.py
│   ├── test_performance_agent.py
│   ├── test_graph.py
│   ├── run_evaluation.py
│   └── migrate_to_pgvector.py
├── evaluation/
│   ├── test_snippets/
│   │   ├── security/
│   │   ├── architecture/
│   │   ├── performance/
│   │   └── clean/
│   └── results/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── llm/
│   │   ├── __init__.py
│   │   └── azure_client.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── session.py
│   │   ├── review.py
│   │   ├── finding.py
│   │   ├── chat_message.py
│   │   └── knowledge_chunk.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── review.py
│   │   ├── chat.py
│   │   └── session.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── security_agent.py
│   │   ├── architecture_agent.py
│   │   ├── performance_agent.py
│   │   ├── code_analyzer.py
│   │   ├── synthesizer.py
│   │   └── chat_agent.py
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py
│   │   ├── nodes.py
│   │   └── builder.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── chunker.py
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   └── retriever.py
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── local_storage.py
│   │   └── db_storage.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── dependencies.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── sessions.py
│   │       ├── reviews.py
│   │       └── chat.py
│   └── utils/
│       ├── __init__.py
│       ├── github.py
│       ├── token_counter.py
│       └── llm_logger.py
└── tests/
    ├── __init__.py
    ├── test_retriever.py
    ├── test_agents.py
    ├── test_graph.py
    └── test_api.py
```

---

## Storage Strategy

Local-first approach. Database comes last as a production upgrade.

| Data                  | Local (Steps 1-15)            | Production (Step 16)         |
| --------------------- | ----------------------------- | ---------------------------- |
| Knowledge source docs | `media/knowledge_base/`       | Stays here permanently       |
| Vector index          | `media/vector_store/` (FAISS) | PostgreSQL + pgvector        |
| Sessions and reviews  | `media/sessions/` (JSON)      | PostgreSQL                   |
| Chat history          | `media/sessions/` (JSON)      | PostgreSQL                   |
| LangGraph state       | InMemorySaver                 | AsyncPostgresSaver           |
| LLM logs              | `media/logs/` (JSONL)         | Stays as files (optional DB) |

---

## Step 1 — Project Scaffolding

**Goal:** Clean project structure, virtual environment, all configs in place.

### Tasks

- [ ] Create the full folder structure shown above
- [ ] Set up Python 3.12.3 virtual environment
- [ ] Install all dependencies from `requirements.txt`
- [ ] Create `.env` file with Azure OpenAI credentials
- [ ] Create `src/config.py` using `pydantic-settings` (`BaseSettings` class) to load all env vars
- [ ] Create `.gitignore` covering `.env`, `__pycache__`, `venv/`, `media/vector_store/`, `media/sessions/`, `media/logs/`, `.ruff_cache`
- [ ] Create empty `media/` subfolders: `knowledge_base/`, `vector_store/`, `sessions/`, `logs/`

### Key File: `src/config.py`

Uses `pydantic-settings` `BaseSettings` to load and validate:

- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_DEPLOYMENT_NAME` (for GPT-4o)
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME`
- `DATABASE_URL` (optional, for Step 16)
- `GITHUB_TOKEN` (optional, for Step 13)
- `MEDIA_DIR` (defaults to `./media`)

### Done When

```bash
python -c "from src.config import settings; print(settings.AZURE_OPENAI_ENDPOINT)"
# prints your Azure endpoint
```

---

## Step 2 — Azure OpenAI Connection

**Goal:** Confirm LLM and embedding model calls work.

### Tasks

- [ ] Create `src/llm/azure_client.py`
- [ ] Initialize `AzureChatOpenAI` from `langchain-openai` with deployment name, API version, endpoint, key
- [ ] Initialize `AzureOpenAIEmbeddings` for embedding deployment
- [ ] Create `scripts/test_llm.py` — sends a simple prompt, prints response
- [ ] Test embedding generation — send sample text, verify vector length (1536 for ada-002)

### Key Classes to Use

- `langchain_openai.AzureChatOpenAI` — for chat completions
- `langchain_openai.AzureOpenAIEmbeddings` — for embeddings

### Done When

Both chat completion and embedding generation return valid results from Azure.

---

## Step 3 — Knowledge Base Collection

**Goal:** Gather raw documents that RAG agents will reference.

### Tasks

- [ ] Create categorized markdown files in `media/knowledge_base/`
- [ ] Write or curate 3-5 solid documents per category
- [ ] Each document should cover: concept, why it is bad, code examples of violations, how to fix

### Folder Structure

```
media/knowledge_base/
├── security/
│   ├── owasp_top_10.md
│   ├── cwe_top_25.md
│   ├── python_security_pitfalls.md
│   └── common_injection_patterns.md
├── architecture/
│   ├── solid_principles.md
│   ├── design_patterns_violations.md
│   ├── clean_code_principles.md
│   └── python_antipatterns.md
└── performance/
    ├── python_performance_antipatterns.md
    ├── async_pitfalls.md
    ├── database_query_patterns.md
    └── memory_and_complexity.md
```

### Content Guidelines

- Start with 10-15 well-written documents total — quality over quantity
- Include real code examples showing both the bad pattern and the fix
- Tag by category — the folder name becomes metadata during ingestion

### Done When

At least 10-15 knowledge documents exist covering the major issues each agent should catch.

---

## Step 4 — Chunking and Local Vector Store

**Goal:** Ingest knowledge base into a local FAISS vector store.

### Tasks

- [ ] Create `src/rag/chunker.py` — reads files from `media/knowledge_base/`, uses `RecursiveCharacterTextSplitter`
- [ ] Create `src/rag/embeddings.py` — wrapper around `AzureOpenAIEmbeddings`
- [ ] Create `src/rag/vector_store.py` — FAISS-based store with `build_index()`, `load_index()`, `save_index()`
- [ ] Create `scripts/ingest_knowledge.py` — orchestrates: read → chunk → embed → store → save to `media/vector_store/`

### Chunking Config

- Chunk size: 500-800 tokens
- Chunk overlap: 100 tokens
- Each chunk carries metadata: `source` (filename), `category` (security/architecture/performance), `chunk_index`

### Dependencies

- `langchain-text-splitters` for `RecursiveCharacterTextSplitter`
- `langchain-community` for `FAISS` vector store (install: `pip install faiss-cpu`)

### Done When

```bash
python scripts/ingest_knowledge.py
# Output: "Processed 15 docs, created 120 chunks, index saved to media/vector_store/"
```

Querying "SQL injection prevention" returns relevant security chunks.

---

## Step 5 — RAG Retriever

**Goal:** A clean retriever interface any agent can call.

### Tasks

- [ ] Create `src/rag/retriever.py` with a `KnowledgeRetriever` class
- [ ] Implement category-filtered similarity search
- [ ] Add convenience methods per agent category
- [ ] Write a test script to verify filtering works

### KnowledgeRetriever Interface

```
class KnowledgeRetriever:
    __init__(index_path)          → loads FAISS index from media/vector_store/
    retrieve(query, category, top_k)  → list of relevant chunks with metadata
    retrieve_for_security(query)      → filtered to category="security"
    retrieve_for_architecture(query)  → filtered to category="architecture"
    retrieve_for_performance(query)   → filtered to category="performance"
```

### Done When

```bash
retriever.retrieve_for_security("hardcoded password in source code")
# returns relevant OWASP/CWE chunks
```

---

## Step 6 — Pydantic Schemas

**Goal:** Define every data structure before writing agent logic.

### Tasks

- [ ] Create `src/schemas/review.py` — `CodeInput`, `Finding`, `AgentOutput`, `ReviewResult`
- [ ] Create `src/schemas/chat.py` — `ChatMessage`, `ChatRequest`, `ChatResponse`
- [ ] Create `src/schemas/session.py` — `Session`
- [ ] Define `Severity` and `Category` as Python `Enum` classes

### Schema Definitions

**Severity Enum:** `critical`, `warning`, `info`

**Category Enum:** `security`, `architecture`, `performance`, `style`

**Finding:**

- `id` — unique identifier
- `agent_name` — which agent found this
- `severity` — Severity enum
- `category` — Category enum
- `title` — short description
- `description` — detailed explanation
- `line_number` — optional, affected line
- `suggestion` — how to fix it
- `source_reference` — optional, which knowledge doc backed this finding

**AgentOutput:**

- `agent_name` — str
- `findings` — list of Finding
- `raw_reasoning` — optional, the LLM's chain of thought

**ReviewResult:**

- `session_id` — str
- `code_snippet_preview` — first 200 chars of submitted code
- `language` — str
- `findings` — list of Finding (merged from all agents)
- `summary` — high-level summary paragraph
- `reviewed_at` — timestamp

### Done When

All schemas can be instantiated with sample data and validate correctly. These become the contract between every component.

---

## Step 7 — Individual Agents

**Goal:** Build each specialist agent independently, testable on its own.

### Tasks

- [ ] Create `src/agents/base.py` — abstract `BaseAgent` class
- [ ] Create `src/agents/security_agent.py`
- [ ] Create `src/agents/architecture_agent.py`
- [ ] Create `src/agents/performance_agent.py`
- [ ] Create `src/agents/code_analyzer.py`
- [ ] Create `src/agents/synthesizer.py`
- [ ] Write standalone test scripts for each agent in `scripts/`

### BaseAgent Design

```
class BaseAgent (abstract):
    agent_name: str
    category: str
    async analyze(code, language) → AgentOutput

    Internally:
    1. Build a system prompt specific to this agent's role
    2. Call retriever for this agent's category
    3. Construct the full prompt: system + retrieved context + user code
    4. Call Azure OpenAI
    5. Parse response into structured Finding objects
    6. Return AgentOutput
```

### Agent Details

**Security Agent:**

- System prompt: "You are a security code reviewer specializing in identifying vulnerabilities..."
- RAG source: `category="security"` (OWASP, CWE)
- Looks for: SQL injection, hardcoded secrets, insecure deserialization, missing input validation, XSS

**Architecture Agent:**

- System prompt: "You are a software architecture reviewer specializing in clean code..."
- RAG source: `category="architecture"` (SOLID, design patterns)
- Looks for: SOLID violations, god classes, tight coupling, naming issues, missing abstractions

**Performance Agent:**

- System prompt: "You are a performance engineer specializing in code efficiency..."
- RAG source: `category="performance"` (antipatterns, complexity)
- Looks for: N+1 queries, blocking I/O in async, unnecessary loops, missing caching, memory issues

**Code Analyzer (no RAG):**

- Detects language if not provided
- Counts functions/classes
- Estimates complexity
- Returns metadata dict to help orchestrator decide which agents to invoke

**Synthesizer:**

- Takes all AgentOutput objects as input
- Merges findings and removes duplicates
- Resolves conflicts (e.g., same issue flagged at different severities)
- Assigns final priority ordering
- Produces the final ReviewResult

### Structured Output Strategy

Instruct each agent's LLM call to return findings in a specific JSON schema. Parse and validate using Pydantic. If parsing fails, retry once with a correction prompt.

### Done When

Each agent independently produces structured findings for a sample code snippet. Synthesizer correctly merges outputs from all three agents.

---

## Step 8 — LangGraph Orchestration

**Goal:** Wire all agents into a LangGraph graph with parallel execution.

### Tasks

- [ ] Create `src/graph/state.py` — define `GraphState` TypedDict
- [ ] Create `src/graph/nodes.py` — async node functions for each agent
- [ ] Create `src/graph/builder.py` — build and compile the StateGraph
- [ ] Write `scripts/test_graph.py` — end-to-end test through the full graph

### GraphState Definition

```
GraphState (TypedDict):
    code: str
    language: str
    code_analysis: dict                    # from code_analyzer
    security_findings: AgentOutput | None
    architecture_findings: AgentOutput | None
    performance_findings: AgentOutput | None
    final_review: ReviewResult | None
    chat_history: list[ChatMessage]
    session_id: str
```

### Graph Flow

```
START
  │
  ▼
[Code Analyzer]
  │
  ├──────────────┬──────────────┐
  ▼              ▼              ▼
[Security]   [Architecture]  [Performance]     ← PARALLEL (fan-out)
  │              │              │
  └──────────────┴──────────────┘
                 │
                 ▼
          [Synthesizer]
                 │
                 ▼
               END
```

### Key Design Decisions

- Use LangGraph's `Send` API or fan-out pattern for parallel agent execution
- Use `InMemorySaver` as the checkpointer for now (will swap to `AsyncPostgresSaver` in Step 16)
- Each node is an async function that takes `GraphState` and returns a partial state update

### Done When

```bash
python scripts/test_graph.py
# submits sample code → all 3 agents run in parallel → synthesizer merges → prints final review
```

---

## Step 9 — Local Session Storage

**Goal:** Persist sessions, reviews, and chat history to `media/` folder as JSON.

### Tasks

- [ ] Create `src/storage/base.py` — abstract storage interface
- [ ] Create `src/storage/local_storage.py` — JSON file-based implementation

### Abstract Interface

```
class BaseSessionStore (abstract):
    async create_session(session_id) → Session
    async save_review(session_id, review) → None
    async get_review(session_id) → ReviewResult
    async save_findings(session_id, findings) → None
    async add_chat_message(session_id, message) → None
    async get_chat_history(session_id) → list[ChatMessage]
    async list_sessions() → list[Session]
    async delete_session(session_id) → None
```

### Local Implementation

- Each session gets a folder: `media/sessions/{session_id}/`
- Files inside: `session.json`, `review.json`, `findings.json`, `chat_history.json`
- Read/write using `aiofiles` or standard `json` module
- The abstract interface allows swapping to database-backed storage later without changing any calling code

### Done When

You can create a session, save a review, add chat messages, and read everything back from JSON files.

---

## Step 10 — Follow-Up Conversation Support

**Goal:** Users can chat about the review findings after the initial analysis.

### Tasks

- [ ] Create `src/agents/chat_agent.py`
- [ ] Update LangGraph graph with conditional entry point
- [ ] Implement chat history loading and token management

### Chat Agent Design

- Receives: user's follow-up message, previous review findings, chat history
- Uses RAG if the question is about a specific topic
- Has access to original code and all findings as context
- Responds conversationally, grounded in review findings

### Conditional Routing in LangGraph

```
Input has 'code'    → full pipeline (analyze → agents → synthesize)
Input has 'message' → route to chat_agent node directly
```

### Token Management

- Load chat history from local storage before each invocation
- If chat history exceeds ~3000 tokens, summarize older messages
- Keep summary + recent messages as context

### Done When

After a review, you can ask "explain finding #2 in more detail" and get a contextual response. Then ask "how do I fix it?" and it remembers the discussion.

---

## Step 11 — FastAPI Endpoints

**Goal:** Expose everything through a REST API.

### Tasks

- [ ] Create `src/api/main.py` — FastAPI app with CORS and lifespan events
- [ ] Create `src/api/dependencies.py` — dependency injection
- [ ] Create `src/api/routes/sessions.py`
- [ ] Create `src/api/routes/reviews.py`
- [ ] Create `src/api/routes/chat.py`

### Endpoints

**Sessions:**

```
POST   /sessions                         → create new session, returns session_id
GET    /sessions                         → list all sessions
GET    /sessions/{session_id}            → get session details
DELETE /sessions/{session_id}            → delete session and all related data
```

**Reviews:**

```
POST   /sessions/{session_id}/review     → submit code for review, triggers full pipeline
GET    /sessions/{session_id}/review     → get saved review result
GET    /sessions/{session_id}/findings   → get findings (filterable by severity, category, agent)
```

**Chat:**

```
POST   /sessions/{session_id}/chat       → send follow-up message, returns AI response
GET    /sessions/{session_id}/chat/history → get full conversation history
```

### Error Handling

| Scenario          | Status Code              |
| ----------------- | ------------------------ |
| Session not found | 404                      |
| Code too long     | 422 with message         |
| LLM call failure  | 502 with readable error  |
| Validation errors | 422 (Pydantic automatic) |

### Done When

```bash
uvicorn src.api.main:app --reload
# Swagger UI at http://localhost:8000/docs
# Full review flow works through the API
```

---

## Step 12 — Streaming Responses

**Goal:** Stream agent findings as they complete instead of waiting for full pipeline.

### Tasks

- [ ] Create streaming endpoint `POST /sessions/{session_id}/review/stream`
- [ ] Use LangGraph's `.astream()` or `.astream_events()`
- [ ] Implement SSE using `sse-starlette`

### SSE Event Types

```
event: code_analysis         → code analyzer finished
event: security_findings     → security agent finished
event: architecture_findings → architecture agent finished
event: performance_findings  → performance agent finished
event: review_complete       → synthesizer finished, final review ready
```

### Done When

A client connecting to the stream endpoint sees findings appear one-by-one as each agent completes.

---

## Step 13 — GitHub URL Support

**Goal:** Accept public GitHub file or PR URLs and fetch code automatically.

### Tasks

- [ ] Create `src/utils/github.py`
- [ ] Update review endpoint to accept `github_url` parameter

### GitHub Utility Functions

```
parse_github_url(url)                    → detect if file URL, raw URL, or PR URL
fetch_file_content(url)                  → convert to raw.githubusercontent.com, fetch with httpx
fetch_pr_files(owner, repo, pr_number)   → GitHub REST API, get changed files and diffs
```

### Notes

- Public repos need no authentication
- For private repos or higher rate limits, use `GITHUB_TOKEN` from env
- For PR URLs, review each changed file or the combined diff

### Done When

Pass a public GitHub file URL to the review endpoint and get a review back.

---

## Step 14 — Logging and Observability

**Goal:** Track every LLM call for debugging, cost tracking, and evaluation.

### Tasks

- [ ] Create `src/utils/llm_logger.py` — logs every LLM call as JSON lines
- [ ] Create `src/utils/token_counter.py` — token counting and cost tracking
- [ ] Add request-level logging in FastAPI

### LLM Call Log Format (JSONL)

```json
{
  "timestamp": "2026-08-29T10:30:00Z",
  "agent_name": "security_agent",
  "model": "gpt-4o",
  "prompt_tokens": 1200,
  "completion_tokens": 450,
  "latency_ms": 2300,
  "success": true,
  "session_id": "abc-123"
}
```

### Token Counter

- Use `tiktoken` to count tokens before sending
- Warn if approaching context window limits
- Track cumulative cost per session

### Done When

After running a few reviews, `media/logs/llm_calls.jsonl` contains a full trace of every LLM interaction.

---

## Step 15 — Evaluation Benchmark

**Goal:** Prove the system works with measurable results.

### Tasks

- [ ] Write 10-15 test code snippets with known issues in `evaluation/test_snippets/`
- [ ] Create `scripts/run_evaluation.py`
- [ ] Save results in `evaluation/results/`

### Test Snippet Categories

- 3-4 snippets with **security vulnerabilities** (SQL injection, hardcoded secrets, XSS)
- 3-4 snippets with **architecture problems** (god class, tight coupling, SOLID violations)
- 3-4 snippets with **performance antipatterns** (N+1, blocking in async, unnecessary loops)
- 2-3 snippets with **clean code** (should get few or no findings)

### Evaluation Metrics

- **Recall per category:** did the system catch the expected issues?
- **Precision:** did it avoid false positives on clean code?
- **Overall score:** percentage of known issues correctly identified

### Interview Value

"I evaluated my system and it catches 85% of known security vulnerabilities in my test set with 90% precision."

### Done When

Repeatable benchmark with saved results showing detection accuracy per category.

---

## Step 16 — Database Migration

**Goal:** Replace local file storage with PostgreSQL + pgvector.

### Sub-Steps

### 16.1 — Docker Compose

- [ ] Create `docker-compose.yml` with `postgres` service (use `pgvector/pgvector:pg16` image) and `app` service
- [ ] Run `CREATE EXTENSION vector;` in Postgres init script

### 16.2 — SQLAlchemy Models

- [ ] Create `src/models/session.py` — Session model
- [ ] Create `src/models/review.py` — Review model
- [ ] Create `src/models/finding.py` — Finding model with severity and category as PG enums
- [ ] Create `src/models/chat_message.py` — ChatMessage model
- [ ] Create `src/models/knowledge_chunk.py` — with `Vector(1536)` column from pgvector
- [ ] Create `src/database.py` — async engine and async session factory

### 16.3 — Alembic Migrations

- [ ] Init Alembic with async support
- [ ] Configure `env.py` with `create_async_engine` and `run_sync()`
- [ ] Generate initial migration from models
- [ ] Run migration to create all tables

### 16.4 — Swap Storage Layer

- [ ] Create `src/storage/db_storage.py` — implements same abstract interface as `LocalSessionStore` using async SQLAlchemy
- [ ] Swap dependency in `src/api/dependencies.py`

### 16.5 — Swap Vector Store to pgvector

- [ ] Update `src/rag/vector_store.py` to use pgvector
- [ ] Similarity search uses `<=>` cosine distance operator in SQL
- [ ] Category filtering in `WHERE` clause
- [ ] Create HNSW index on embedding column
- [ ] Create `scripts/migrate_to_pgvector.py` — reads FAISS index, bulk-inserts into pgvector

### 16.6 — Swap LangGraph Checkpointer

- [ ] Replace `InMemorySaver` with `AsyncPostgresSaver` from `langgraph-checkpoint-postgres`
- [ ] Uses `psycopg3` connection string
- [ ] Call `.setup()` on first run to create checkpointer tables

### Database Driver Note

Two PostgreSQL drivers coexist in this project:

| Driver            | Used By                        | Purpose                                                            |
| ----------------- | ------------------------------ | ------------------------------------------------------------------ |
| `psycopg[binary]` | LangGraph `AsyncPostgresSaver` | Graph state and conversation checkpoints                           |
| `asyncpg`         | SQLAlchemy async engine        | Application tables (sessions, reviews, findings, knowledge_chunks) |

Both connect to the same PostgreSQL instance — no conflict.

### Done When

Entire app runs against PostgreSQL. Local `media/` folder is only needed for knowledge base source files and logs.

---

## Step 17 — README and Portfolio Polish

**Goal:** Make the repo interview-ready.

### Tasks

- [ ] Draw architecture diagram (Mermaid or Excalidraw)
- [ ] Draw sequence diagram for a single review request
- [ ] Write comprehensive README

### README Sections

- [ ] Project overview — the elevator pitch
- [ ] Architecture diagram
- [ ] Tech stack with justifications
- [ ] Setup instructions (Docker Compose one-command start)
- [ ] API documentation (or link to Swagger)
- [ ] Example request and response
- [ ] Evaluation results
- [ ] Design decisions section
- [ ] Future improvements

### Demo Recording

Record a 2-minute screen capture showing:

1. Start the app with Docker Compose
2. Open Swagger UI
3. Submit a vulnerable code snippet
4. Show the structured review
5. Ask a follow-up question
6. Show the conversation flow

### Done When

Someone landing on your GitHub repo can understand, run, and be impressed by the project within 5 minutes.

---

## Environment Variables

```env
# ---- Azure OpenAI ----
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-10-21
AZURE_OPENAI_DEPLOYMENT_NAME=your-gpt4o-deployment
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=your-embedding-deployment

# ---- Database (Step 16 onwards) ----
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/codelens
POSTGRES_URI=postgresql://user:pass@localhost:5432/codelens

# ---- GitHub (Optional, Step 13) ----
GITHUB_TOKEN=ghp_your_personal_access_token

# ---- App Config ----
MEDIA_DIR=./media
LOG_LEVEL=INFO
```

---

> **Start at Step 1. Each step builds on the previous one. Each step is independently testable. You will have a working, demo-ready project by Step 15, with the database migration in Step 16 as the production-grade upgrade.**
