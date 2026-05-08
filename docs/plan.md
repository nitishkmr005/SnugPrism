SnugPrism — DS Interview Prep Web App                                                                                                                                                                                                                                                                                                                                                                                                               
                                                                                                                             
 Context                             

 Nitish Harsoor (10 years at Fidelity Investments, senior data scientist with deep expertise in
 LLMs, RAG, Recommender Systems, Voice Agents, and Production ML) needs a personal interview
 preparation app to land AI Engineering / ML Engineering / Data Scientist roles at top AI companies
 within 3 months. The app must be a mobile-accessible, single-place study hub with:
 - Curated Q&A pairs seeded from his actual work experience and standard DS interview topics
 - Document ingestion (PDF + URL) to add new material via mobile
 - A RAG-powered chatbot for clarifying doubts
 - A structured Learning Hub for deep dives
 - Clean REST API so his separate voice agent repo can plug in

 No authentication required (personal use).

 ---
 Architecture Overview

 ┌─────────────────────────────────────┐     ┌───────────────────────────────────┐
 │  Frontend — Next.js 14 (Vercel)     │────▶│  Backend — FastAPI (Railway)      │
 │  TypeScript · Tailwind · shadcn/ui  │     │  Python 3.12 · uv · pdfplumber    │
 │                                     │     │  OpenAI GPT-4o · text-emb-3-small │
 │  /prep   — FAQ Q&A browser          │     │  Supabase pgvector (RAG)          │
 │  /hub    — Learning Hub (tabs)      │     │  Tavily (web search)              │
 │  /ingest — PDF/URL ingestion UI     │     │                                   │
 │  ChatWidget (floating, all pages)   │     │  /api/questions, /api/chat        │
 └─────────────────────────────────────┘     │  /api/ingest, /api/hub, /api/topics│
                                             └───────────────────────────────────┘
                                                            │
                                             ┌──────────────▼──────────────────────┐
                                             │  Supabase (PostgreSQL + pgvector)   │
                                             │  topics, questions, documents        │
                                             │  chunks (1536-dim embeddings)        │
                                             │  hub_sections, chat_messages         │
                                             └─────────────────────────────────────┘

 Voice agent (separate repo) → calls POST /api/chat with stream:false + X-API-Key header

 ---
 Project Structure

 snugprism/
 ├── CLAUDE.md
 ├── README.md
 ├── Makefile
 ├── .gitignore
 ├── docs/
 │   └── voice_agent_integration.md
 │
 ├── backend/                          ← Railway (FastAPI)
 │   ├── pyproject.toml
 │   ├── uv.lock
 │   ├── Dockerfile
 │   ├── .env.example
 │   ├── railway.json
 │   ├── logs/
 │   ├── data/
 │   │   ├── pdfs/                     ← uploaded + seeded PDFs
 │   │   └── seed/
 │   │       └── questions.json        ← 30 handcrafted bootstrap Q&As
 │   ├── scripts/
 │   │   ├── seed_db.py                ← one-shot: seeds questions + hub content
 │   │   ├── ingest_pdf.py             ← educational standalone
 │   │   └── test_rag.py               ← standalone RAG smoke test
 │   ├── config/
 │   │   ├── settings.py               ← Pydantic BaseSettings (single source of truth)
 │   │   └── logging.py                ← loguru: terminal + JSON file rotation (max 5)
 │   └── app/
 │       ├── main.py                   ← FastAPI app factory + CORS
 │       ├── models.py                 ← shared Pydantic request/response models
 │       ├── prompts/
 │       │   ├── qa_generation.py      ← GPT-4o Q&A generation prompt (depth-focused)
 │       │   └── rag_chat.py           ← RAG system prompt (cites sources)
 │       ├── routers/
 │       │   ├── health.py
 │       │   ├── topics.py             ← GET /api/topics
 │       │   ├── questions.py          ← CRUD /api/questions
 │       │   ├── chat.py               ← POST /api/chat (stream + non-stream)
 │       │   ├── ingest.py             ← POST /api/ingest/pdf + /url + GET status
 │       │   └── hub.py                ← GET /api/hub/{topic_slug}
 │       └── services/
 │           ├── llm.py                ← provider-agnostic (openai|anthropic)
 │           ├── embeddings.py         ← provider-agnostic (openai|local)
 │           ├── db.py                 ← Supabase async client wrapper
 │           ├── rag.py                ← embed query → pgvector search → assemble context → LLM
 │           ├── pdf_processor.py      ← pdfplumber text extraction + page mapping
 │           ├── url_scraper.py        ← httpx + BeautifulSoup4
 │           ├── qa_generator.py       ← orchestrates: extract → chunk → embed → GPT-4o → store
 │           └── web_search.py         ← Tavily API wrapper (falls back to empty list)
 │
 └── frontend/                         ← Vercel (Next.js 14 App Router)
     ├── package.json
     ├── tsconfig.json
     ├── next.config.ts
     ├── tailwind.config.ts
     ├── .env.local.example
     ├── vercel.json
     └── src/
         ├── app/
         │   ├── globals.css
         │   ├── layout.tsx            ← root layout: Navbar + ChatWidget (always mounted)
         │   ├── page.tsx              ← redirect → /prep
         │   ├── prep/page.tsx         ← Interview Prep FAQ
         │   ├── hub/page.tsx          ← Learning Hub
         │   └── ingest/page.tsx       ← Document Ingestion
         ├── components/
         │   ├── layout/
         │   │   └── Navbar.tsx        ← Prep | Hub | Ingest links
         │   ├── prep/
         │   │   ├── QuestionCard.tsx  ← expandable Q&A + code + table + refs + PDF links
         │   │   ├── QuestionList.tsx  ← scrollable list (react-virtual for performance)
         │   │   ├── TopicSidebar.tsx  ← topic filter pills from /api/topics
         │   │   ├── SearchBar.tsx     ← debounced (300ms) client-side filter
         │   │   ├── DifficultyBadge.tsx
         │   │   ├── CodeBlock.tsx     ← shiki syntax highlighting
         │   │   └── ComparisonTable.tsx
         │   ├── hub/
         │   │   ├── TopicTabs.tsx
         │   │   ├── SubSection.tsx    ← markdown content block
         │   │   └── DiagramBlock.tsx  ← Mermaid renderer
         │   ├── ingest/
         │   │   ├── PdfUploader.tsx   ← drag-drop + mobile file picker
         │   │   ├── UrlIngester.tsx
         │   │   ├── TopicSelector.tsx ← multi-select checkboxes
         │   │   └── IngestStatus.tsx  ← polls /api/ingest/status every 2s
         │   └── chat/
         │       ├── ChatWidget.tsx    ← floating bottom-right FAB
         │       ├── ChatPanel.tsx     ← message list + input
         │       ├── ChatMessage.tsx   ← user/assistant bubbles
         │       └── ArticleCard.tsx   ← web search result inline card
         └── lib/
             ├── api.ts                ← typed API client (React Query hooks)
             └── types.ts              ← shared TypeScript interfaces

 ---
 Database Schema (Supabase)

 create extension if not exists vector;

 create table topics (
     id         serial primary key,
     slug       text unique not null,  -- "llms", "recommender_systems", etc.
     label      text not null,
     sort_order int default 0
 );
 -- 9 rows: sql, statistics, ml_models, recommender_systems, llms,
 --         ai_agents, embedding_models, llm_inferencing, evaluation

 create table questions (
     id               uuid primary key default gen_random_uuid(),
     topic_id         int references topics(id),
     question         text not null,
     answer           text not null,          -- markdown
     difficulty       text check (difficulty in ('easy','medium','hard')),
     tags             text[] default '{}',
     code_snippet     text,                   -- fenced markdown code block or null
     comparison_table jsonb,                  -- {headers:[], rows:[[...]]} or null
     reference_urls   text[] default '{}',
     pdf_links        jsonb default '[]',     -- [{doc_id, page, label}]
     source           text default 'manual',  -- 'manual'|'generated'|'seeded'
     created_at       timestamptz default now()
 );
 create index on questions(topic_id);
 create index on questions using gin(to_tsvector('english', question || ' ' || answer));

 create table documents (
     id          uuid primary key default gen_random_uuid(),
     title       text not null,
     source_type text check (source_type in ('pdf','url')),
     source_ref  text not null,               -- filename or URL
     topic_ids   int[] default '{}',
     chunk_count int default 0,
     ingested_at timestamptz default now()
 );

 create table chunks (
     id          uuid primary key default gen_random_uuid(),
     doc_id      uuid references documents(id) on delete cascade,
     chunk_index int not null,
     content     text not null,
     page_number int,
     embedding   vector(1536)                 -- text-embedding-3-small
 );
 -- After bulk seed: create index on chunks using hnsw (embedding vector_cosine_ops)
 -- with (m=16, ef_construction=64);

 create table chat_sessions (
     id      uuid primary key default gen_random_uuid(),
     source  text default 'web',              -- 'web' | 'voice_agent'
     created_at timestamptz default now()
 );

 create table chat_messages (
     id         uuid primary key default gen_random_uuid(),
     session_id uuid references chat_sessions(id) on delete cascade,
     role       text check (role in ('user','assistant')),
     content    text not null,
     sources    jsonb default '[]',           -- [{chunk_id, score, content_preview}]
     articles   jsonb default '[]',           -- [{title, url, snippet}]
     created_at timestamptz default now()
 );
 create index on chat_messages(session_id);

 create table hub_sections (
     id          serial primary key,
     topic_id    int references topics(id) on delete cascade,
     title       text not null,
     content     text not null,              -- markdown
     sort_order  int default 0,
     diagram_def text                        -- Mermaid syntax or null
 );
 create index on hub_sections(topic_id);

 ---
 API Endpoints

 GET  /api/health
 GET  /api/topics
 GET  /api/questions?topic_slug=&difficulty=&q=&limit=50&offset=0
 GET  /api/questions/{id}
 POST /api/questions
 PUT  /api/questions/{id}
 DELETE /api/questions/{id}

 POST /api/chat          body: {message, session_id?, stream?, include_web_search?, format?}
                         stream:true  → SSE (event: token|sources|articles|done)
                         stream:false → {session_id, reply, sources, articles}
                         format:"text" → strips markdown for voice TTS
 GET  /api/chat/sessions/{session_id}/history

 POST /api/ingest/pdf    multipart: file, topic_ids, generate_qa=true
 POST /api/ingest/url    body: {url, topic_ids, generate_qa}
 GET  /api/ingest/status/{doc_id}
 GET  /api/documents
 GET  /api/documents/{doc_id}/page/{page_num}

 GET  /api/hub/{topic_slug}

 ---
 Key Service Details

 LLM Layer (services/llm.py)

 Provider-agnostic with settings.llm_provider branching. Exposes complete() + stream().
 No provider logic leaks outside this file. Swap openai ↔ anthropic by changing one env var.

 RAG Pipeline (services/rag.py)

 query → embed(query) → pgvector cosine search (top_k=5 chunks)
       → optional: tavily web_search(query, max_results=3)
       → assemble context: [DOC CONTEXT] + [WEB RESULTS] sections
       → messages: [system_prompt, context_msg, last_5_history, user_msg]
       → llm.complete() or llm.stream()
       → persist to chat_messages
       → return {reply, sources, articles}

 Document Processing (services/qa_generator.py)

 PDF/URL → extract text + page map
         → chunk(size=800, overlap=100)
         → embed(chunks) batched at 20/call
         → insert document + chunks to DB
         → if generate_qa: for each topic_id:
               qa_pairs = llm(QA_GENERATION_PROMPT, text[:8000], topic, n=15)
               parse JSON → insert questions

 Q&A Generation Prompt (key design — depth over recall)

 Rules enforced in prompt:
 - Prefer "How would you...?" / "What tradeoffs...?" over "What is...?"
 - Answers: 150-300 words, markdown-formatted
 - Include code_snippet when implementation-heavy
 - Include comparison_table when comparing approaches
 - Difficulty: easy/medium/hard
 - Return ONLY a JSON array

 ---
 Seed Data Strategy

 Bootstrap seed (30 handcrafted Q&As in data/seed/questions.json)

 Questions tailored to Nitish's actual work experience:

 ┌─────────────────────┬───────┬──────────────────────────────────────────┐
 │        Topic        │ Count │                Linked To                 │
 ├─────────────────────┼───────┼──────────────────────────────────────────┤
 │ LLMs                │ 10    │ AgentBot 3.0, LLM-as-a-Judge, extraction │
 ├─────────────────────┼───────┼──────────────────────────────────────────┤
 │ Recommender Systems │ 10    │ Two-tower (WPS), Helios MAB, cold-start  │
 ├─────────────────────┼───────┼──────────────────────────────────────────┤
 │ AI Agents           │ 10    │ AgentBot, Voice Agent, LangGraph         │
 └─────────────────────┴───────┴──────────────────────────────────────────┘

 Auto-generated expansion (scripts/seed_db.py)

 Ingests resume/NitishHarsoorResume_2026.pdf via pdfplumber → GPT-4o generates 15 Q&As
 per topic × 9 topics = ~135 questions. Embeds and stores all.

 ┌──────────────────────────┬──────────────┐
 │          Topic           │ Target Count │
 ├──────────────────────────┼──────────────┤
 │ LLMs                     │ 20           │
 ├──────────────────────────┼──────────────┤
 │ Recommender Systems      │ 18           │
 ├──────────────────────────┼──────────────┤
 │ AI Agents                │ 15           │
 ├──────────────────────────┼──────────────┤
 │ Evaluation (RAG/LLM/Rec) │ 15           │
 ├──────────────────────────┼──────────────┤
 │ Embedding Models         │ 12           │
 ├──────────────────────────┼──────────────┤
 │ LLM Inferencing          │ 10           │
 ├──────────────────────────┼──────────────┤
 │ Statistics               │ 8            │
 ├──────────────────────────┼──────────────┤
 │ ML Models                │ 8            │
 ├──────────────────────────┼──────────────┤
 │ SQL                      │ 6            │
 └──────────────────────────┴──────────────┘

 Learning Hub content

 seed_db.py also generates hub_sections via GPT-4o for all 9 topics, including:
 - Recommenders: Graph-based, DNN Two-Tower, Propensity, MAB/RL, Production deployment
 - LLMs: Architecture, Pre-training, RLHF, Fine-tuning, Evaluation
 - Agents: ReAct, LangGraph, Tool Calling, Memory, Voice Agents
 - Evaluation: RAG metrics (faithfulness/relevance/context recall), LLM-as-a-Judge, A/B testing

 ---
 Voice Agent Integration

 The separate voice agent repo calls these endpoints:

 POST /api/chat
 X-API-Key: {VOICE_AGENT_API_KEY}
 Content-Type: application/json

 {
   "message": "Explain two-tower model in recommender systems",
   "session_id": "voice-abc123",
   "stream": false,
   "include_web_search": false,
   "format": "text"
 }

 Response: {session_id, reply (plain text, no markdown), sources, articles}

 For practice questions: GET /api/questions?topic_slug=llms&difficulty=hard&limit=1

 Security: X-API-Key header validated in FastAPI middleware against VOICE_AGENT_API_KEY env var.

 ---
 Environment Variables

 Backend (Railway)

 OPENAI_API_KEY=
 SUPABASE_URL=
 SUPABASE_SERVICE_ROLE_KEY=
 TAVILY_API_KEY=
 CORS_ORIGINS=http://localhost:3000,https://snugprism.vercel.app
 LLM_PROVIDER=openai
 EMBEDDING_PROVIDER=openai
 VOICE_AGENT_API_KEY=

 Frontend (Vercel)

 NEXT_PUBLIC_API_URL=https://snugprism-backend.up.railway.app

 ---
 Deployment Config

 backend/Dockerfile

 FROM python:3.12-slim
 WORKDIR /app
 RUN pip install uv
 COPY pyproject.toml uv.lock ./
 RUN uv sync --frozen --no-dev
 COPY . .
 EXPOSE 8000
 CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

 backend/railway.json

 {
   "build": { "builder": "DOCKERFILE", "dockerfilePath": "backend/Dockerfile" },
   "deploy": { "restartPolicyType": "ON_FAILURE" }
 }

 ---
 Implementation Order

 Phase 1 — Backend Foundation (Days 1–2)

 1. git init snugprism, monorepo skeleton, uv init backend
 2. config/settings.py + config/logging.py — verify: settings print correctly
 3. app/main.py bare FastAPI + health router — verify: curl /api/health → 200
 4. services/db.py Supabase client — verify: connects to Supabase
 5. Run schema SQL in Supabase — verify: all 7 tables created
 6. Seed topics table (9 rows)

 Phase 2 — Data Layer (Days 3–4)

 7. services/llm.py + services/embeddings.py — verify: embed() returns 1536-dim vector
 8. services/pdf_processor.py — verify: extracts text from resume PDF with page numbers
 9. services/url_scraper.py — verify: scrapes a DS blog post
 10. Write data/seed/questions.json (30 questions) — verify: valid JSON
 11. scripts/seed_db.py — verify: 30 rows in questions table in Supabase

 Phase 3 — RAG + Chat (Days 5–6)

 12. services/rag.py similarity search — verify: query "two-tower" returns relevant chunks
 13. services/web_search.py — verify: Tavily returns 3 articles for a DS query
 14. app/routers/chat.py streaming + non-streaming — verify: both modes return coherent answers

 Phase 4 — Ingestion Pipeline (Day 7)

 15. services/qa_generator.py full pipeline
 16. app/routers/ingest.py with BackgroundTasks — verify: upload PDF, status goes "processing"→"done"
 17. scripts/seed_db.py resume ingestion — verify: ~135 Q&As generated in DB

 Phase 5 — Frontend Skeleton (Days 8–9)

 18. create-next-app + install shadcn/ui, shiki, mermaid, @tanstack/react-query
 19. Navbar.tsx + root layout.tsx
 20. TopicSidebar.tsx fetching /api/topics — verify: 9 topic pills render

 Phase 6 — Prep Page (Days 10–11)

 21. QuestionCard.tsx + QuestionList.tsx wired to /api/questions
 22. CodeBlock.tsx (shiki) + ComparisonTable.tsx
 23. SearchBar.tsx debounced filter — verify: search "transformer" filters cards

 Phase 7 — Hub Page + Ingest Page (Days 12–13)

 24. TopicTabs.tsx + SubSection.tsx + DiagramBlock.tsx (Mermaid)
 25. PdfUploader.tsx + UrlIngester.tsx + IngestStatus.tsx — verify: works on mobile

 Phase 8 — Chat Widget (Days 14–15)

 26. ChatWidget.tsx floating FAB + ChatPanel.tsx
 27. SSE streaming via EventSource
 28. ArticleCard.tsx inline article cards

 Phase 9 — Hub Content Seeding (Day 16)

     Phase 9 — Hub Content Seeding (Day 16)

     29. Run seed_db.py hub_sections generation — verify: all 9 Hub tabs populated with GPT-4o content
     30. Add Mermaid diagrams for key topics (Two-Tower arch, RAG pipeline, Agent loop)

     Phase 10 — Deployment (Days 17–18)

     31. Build + test Dockerfile locally
     32. Deploy backend to Railway (set env vars)
     33. Deploy frontend to Vercel (set NEXT_PUBLIC_API_URL)
     34. End-to-end smoke test: ingest URL on phone → Q&As appear in /prep

     Phase 11 — Voice Agent Polish (Day 19)

     35. Add format=text param + X-API-Key middleware
     36. Write docs/voice_agent_integration.md
     37. Verify: curl from voice agent repo returns clean text

     ---
     Verification (End-to-End Tests)

     1. curl https://snugprism-backend.up.railway.app/api/health → {"status":"ok"}
     2. curl /api/questions?topic_slug=llms&difficulty=hard → returns ≥5 questions with code_snippets
     3. Open /prep on phone → scroll Q&As, expand answers, click reference URL
     4. Upload a PDF on /ingest page on phone → status shows "done" → new Q&As in /prep
     5. Add an article URL → Q&As generated and appear under correct topic
     6. Type in ChatWidget: "Explain LinGreedy MAB" → streamed answer with source citations
     7. POST /api/chat with stream:false, format:text, X-API-Key → clean text response for voice agent
     8. Open /hub → all 9 topic tabs have content, Mermaid diagrams render

     ---
     Critical Files to Create First

     ┌──────────┬───────────────────────────────────────────────┬────────────────────────────────────────────────┐
     │ Priority │                     File                      │                      Why                       │
     ├──────────┼───────────────────────────────────────────────┼────────────────────────────────────────────────┤
     │ 1        │ backend/config/settings.py                    │ All services read from here                    │
     ├──────────┼───────────────────────────────────────────────┼────────────────────────────────────────────────┤
     │ 2        │ backend/app/services/llm.py                   │ Provider-agnostic LLM layer used by everything │
     ├──────────┼───────────────────────────────────────────────┼────────────────────────────────────────────────┤
     │ 3        │ backend/app/prompts/qa_generation.py          │ Q&A quality determines the entire seed data    │
     ├──────────┼───────────────────────────────────────────────┼────────────────────────────────────────────────┤
     │ 4        │ backend/app/services/rag.py                   │ Core retrieval pipeline for chatbot            │
     ├──────────┼───────────────────────────────────────────────┼────────────────────────────────────────────────┤
     │ 5        │ frontend/src/components/prep/QuestionCard.tsx │ Primary UI component (90% of study time)       │
     └──────────┴───────────────────────────────────────────────┴────────────────────────────────────────────────┘