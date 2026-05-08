# SnugPrism — AI Engineering Interview Prep

Personal interview prep app for AI/ML Engineering roles. Curated Q&A, document ingestion (PDF + URL), RAG-powered chat, and a Learning Hub with Mermaid diagrams.

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, React 19, TypeScript, Tailwind 4, shadcn/ui |
| Backend | FastAPI, Python 3.12, Pydantic v2 |
| Vector DB | Qdrant (local or Qdrant Cloud) |
| Document DB | MongoDB (local or Atlas) |
| LLM | OpenAI GPT-4o (provider-agnostic layer) |
| Embeddings | text-embedding-3-small (1536-dim) |
| Web Search | Tavily |
| Deployment | Railway (backend) · Vercel (frontend) |

## Features

- **Interview Prep** — 9 topic areas (SQL, Statistics, ML Models, Recommender Systems, LLMs, AI Agents, Embedding Models, LLM Inferencing, Evaluation) with curated Q&A
- **Document Ingestion** — Upload PDFs or paste URLs; auto-generates Q&A from content via GPT-4o
- **RAG Chat** — Streaming chat grounded in your documents; optional Tavily web search
- **Learning Hub** — Topic deep-dives with Mermaid diagrams
- **Voice Agent API** — REST endpoint for voice-agent integration (API-key protected)

## Project Structure

```
snugprism/
├── backend/                 # FastAPI + Python
│   ├── config/
│   │   ├── app.yaml         # Non-secret config (LLM, RAG, CORS, DB defaults)
│   │   ├── settings.py      # Pydantic BaseSettings (reads app.yaml + .env)
│   │   └── logging.py       # loguru setup
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── routers/         # health, topics, questions, hub, chat, ingest
│   │   ├── services/
│   │   │   ├── document_db.py   # MongoDB (Motor async)
│   │   │   ├── vector_db.py     # Qdrant (AsyncQdrantClient)
│   │   │   ├── rag.py           # RAG pipeline
│   │   │   ├── qa_generator.py  # Document → chunks → embeddings → Q&A
│   │   │   ├── llm.py           # Provider-agnostic LLM
│   │   │   └── embeddings.py    # Provider-agnostic embeddings
│   │   └── prompts/
│   ├── scripts/
│   │   └── seed_db.py       # Seed topics + bootstrap Q&As + resume ingestion
│   ├── .env                 # Secrets only (API keys, DB URI with credentials)
│   ├── .env.example         # Template — copy and fill in values
│   └── pyproject.toml
├── frontend/                # Next.js 14 app
└── docs/                    # Architecture docs
```

## Quick Start

### Prerequisites

- Python 3.12+ and `uv`
- Node.js 20+
- MongoDB running locally (`mongod`) or an Atlas URI
- Qdrant running locally (`docker run -p 6333:6333 qdrant/qdrant`) or a Qdrant Cloud cluster

### 1. Clone and configure

```bash
cd backend
cp .env.example .env
# Fill in OPENAI_API_KEY (required) and any other secrets
```

Non-secret config (CORS origins, model names, chunk sizes, etc.) lives in `config/app.yaml` — edit that directly.

### 2. Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
# API available at http://localhost:8000
```

### 3. Seed the database

```bash
cd backend
uv run python scripts/seed_db.py --skip-pdf --skip-hub   # fast: topics + Q&As only
uv run python scripts/seed_db.py                          # full: + resume + hub (needs OPENAI_API_KEY)
```

### 4. Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
# UI available at http://localhost:3000
```

## Developer Commands

```bash
make dev-backend    # Start FastAPI (port 8000)
make dev-frontend   # Start Next.js (port 3000)
make seed           # Seed topics + bootstrap Q&As
make seed-full      # Full seed (requires OPENAI_API_KEY)
make check          # Health check against local backend
make build-backend  # Build Docker image
```

## Infrastructure Setup

### Local Qdrant (Docker)

```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### Local MongoDB

```bash
brew services start mongodb-community  # macOS
# or: mongod --dbpath /usr/local/var/mongodb
```

### Production (Qdrant Cloud + MongoDB Atlas)

Set in `backend/.env`:

```
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/snugprism
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | MongoDB + Qdrant connectivity check |
| GET | `/api/topics` | List all 9 topics |
| GET | `/api/questions` | List questions (filter: topic_slug, difficulty, q) |
| POST | `/api/questions` | Create question |
| POST | `/api/chat` | RAG chat (streaming SSE or JSON) |
| POST | `/api/ingest/pdf` | Upload PDF for ingestion |
| POST | `/api/ingest/url` | Ingest URL |
| GET | `/api/hub/{topic_slug}` | Learning Hub content |

## Configuration

All non-secret config is in `backend/config/app.yaml`. Secrets go in `backend/.env`.

| Config | Location | Examples |
|---|---|---|
| API keys, passwords | `.env` | `OPENAI_API_KEY`, `MONGODB_URI` |
| App settings | `config/app.yaml` | CORS origins, model names, chunk sizes |
| LLM provider swap | `config/app.yaml` → `llm.provider` | `openai` (default) |
| Qdrant local vs cloud | `.env` → `QDRANT_URL` | blank = local |
