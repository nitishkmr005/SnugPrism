-- SnugPrism Supabase Schema
-- Run this in the Supabase SQL Editor (Dashboard → SQL Editor → New query)

-- Enable pgvector extension
create extension if not exists vector;

-- ─────────────────────────────────────────────────────────────────────────────
-- TOPICS
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists topics (
    id         serial primary key,
    slug       text unique not null,
    label      text not null,
    sort_order int not null default 0,
    created_at timestamptz default now()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- QUESTIONS
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists questions (
    id               uuid primary key default gen_random_uuid(),
    topic_id         int references topics(id) on delete restrict,
    question         text not null,
    answer           text not null,
    difficulty       text check (difficulty in ('easy', 'medium', 'hard')) not null default 'medium',
    tags             text[] default '{}',
    code_snippet     text,
    comparison_table jsonb,
    reference_urls   text[] default '{}',
    pdf_links        jsonb default '[]',
    source           text default 'manual',
    created_at       timestamptz default now(),
    updated_at       timestamptz default now()
);

create index if not exists questions_topic_idx on questions(topic_id);
create index if not exists questions_difficulty_idx on questions(difficulty);
create index if not exists questions_fts_idx on questions
    using gin(to_tsvector('english', question || ' ' || answer));

-- ─────────────────────────────────────────────────────────────────────────────
-- DOCUMENTS
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists documents (
    id          uuid primary key default gen_random_uuid(),
    title       text not null,
    source_type text check (source_type in ('pdf', 'url')) not null,
    source_ref  text not null,
    topic_ids   int[] default '{}',
    chunk_count int default 0,
    ingested_at timestamptz default now()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- CHUNKS (vector store for RAG)
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists chunks (
    id          uuid primary key default gen_random_uuid(),
    doc_id      uuid references documents(id) on delete cascade,
    chunk_index int not null,
    content     text not null,
    page_number int,
    embedding   vector(1536),
    created_at  timestamptz default now()
);

-- HNSW index for fast cosine similarity search
-- Run this AFTER the initial bulk insert for better performance
-- create index on chunks using hnsw (embedding vector_cosine_ops)
-- with (m = 16, ef_construction = 64);

-- ─────────────────────────────────────────────────────────────────────────────
-- RPC FUNCTION for vector similarity search
-- ─────────────────────────────────────────────────────────────────────────────
create or replace function match_chunks(
    query_embedding vector(1536),
    match_count int default 5
)
returns table (
    id          uuid,
    doc_id      uuid,
    content     text,
    page_number int,
    similarity  float,
    doc_title   text
)
language sql stable
as $$
    select
        c.id,
        c.doc_id,
        c.content,
        c.page_number,
        1 - (c.embedding <=> query_embedding) as similarity,
        d.title as doc_title
    from chunks c
    join documents d on d.id = c.doc_id
    order by c.embedding <=> query_embedding
    limit match_count;
$$;

-- ─────────────────────────────────────────────────────────────────────────────
-- CHAT
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists chat_sessions (
    id         uuid primary key default gen_random_uuid(),
    source     text default 'web',
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create table if not exists chat_messages (
    id         uuid primary key default gen_random_uuid(),
    session_id uuid references chat_sessions(id) on delete cascade,
    role       text check (role in ('user', 'assistant')) not null,
    content    text not null,
    sources    jsonb default '[]',
    articles   jsonb default '[]',
    created_at timestamptz default now()
);

create index if not exists chat_messages_session_idx on chat_messages(session_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- LEARNING HUB
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists hub_sections (
    id          serial primary key,
    topic_id    int references topics(id) on delete cascade,
    title       text not null,
    content     text not null,
    sort_order  int not null default 0,
    diagram_def text,
    created_at  timestamptz default now()
);

create index if not exists hub_sections_topic_idx on hub_sections(topic_id);
