"""RAG pipeline: embed query → Qdrant search → context assembly → LLM."""
from __future__ import annotations
import re
from loguru import logger
from config.settings import get_settings
from app.services import llm, embeddings, web_search
from app.services.vector_db import search_chunks
from app.services.document_db import (
    create_chat_session,
    fetch_session_messages,
    insert_chat_message,
)
from app.prompts.rag_chat import build_rag_messages


def _strip_markdown(text: str) -> str:
    """Remove markdown formatting for voice-agent plain-text responses."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"#{1,6}\s+", "", text)
    text = re.sub(r"```[\s\S]*?```", "[code block]", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    return text.strip()


async def chat(
    message: str,
    session_id: str | None,
    include_web_search: bool,
    response_format: str,
) -> dict:
    """Non-streaming RAG chat. Returns {session_id, reply, sources, articles}."""
    s = get_settings()

    if not session_id:
        sess = await create_chat_session("web")
        session_id = sess["id"]

    history = await _build_history(session_id)
    query_vec = await embeddings.embed_one(message)
    sources = await search_chunks(query_vec, s.rag_top_k)
    articles: list[dict] = []
    if include_web_search:
        articles = await web_search.search(message)

    doc_context = _format_doc_context(sources)
    web_context = _format_web_context(articles)
    messages = build_rag_messages(message, doc_context, web_context, history)

    reply = await llm.complete(messages)
    if response_format == "text":
        reply = _strip_markdown(reply)

    await insert_chat_message(session_id, "user", message, [], [])
    await insert_chat_message(session_id, "assistant", reply, sources, articles)

    return {
        "session_id": session_id,
        "reply": reply,
        "sources": _clean_sources(sources),
        "articles": articles,
    }


async def chat_stream(
    message: str,
    session_id: str | None,
    include_web_search: bool,
):
    """Streaming RAG chat. Yields SSE-formatted strings."""
    import json
    s = get_settings()

    if not session_id:
        sess = await create_chat_session("web")
        session_id = sess["id"]

    query_vec = await embeddings.embed_one(message)
    sources = await search_chunks(query_vec, s.rag_top_k)
    articles: list[dict] = []
    if include_web_search:
        articles = await web_search.search(message)

    history = await _build_history(session_id)
    doc_context = _format_doc_context(sources)
    web_context = _format_web_context(articles)
    messages = build_rag_messages(message, doc_context, web_context, history)

    full_reply = []
    async for token in llm.stream(messages):
        full_reply.append(token)
        yield f"event: token\ndata: {json.dumps(token)}\n\n"

    reply_text = "".join(full_reply)
    await insert_chat_message(session_id, "user", message, [], [])
    await insert_chat_message(session_id, "assistant", reply_text, sources, articles)

    yield f"event: sources\ndata: {json.dumps(_clean_sources(sources))}\n\n"
    yield f"event: articles\ndata: {json.dumps(articles)}\n\n"
    yield f"event: session\ndata: {json.dumps({'session_id': session_id})}\n\n"
    yield "event: done\ndata: {}\n\n"


async def _build_history(session_id: str) -> list[dict]:
    msgs = await fetch_session_messages(session_id)
    return [{"role": m["role"], "content": m["content"]} for m in msgs[-10:]]


def _format_doc_context(sources: list[dict]) -> str:
    if not sources:
        return ""
    parts = []
    for s in sources:
        preview = s.get("content", "")[:600]
        title = s.get("doc_title", "Study Material")
        parts.append(f"[Source: {title}]\n{preview}")
    return "\n\n".join(parts)


def _format_web_context(articles: list[dict]) -> str:
    if not articles:
        return ""
    return "\n".join(f"- {a['title']}: {a['snippet'][:300]}" for a in articles)


def _clean_sources(sources: list[dict]) -> list[dict]:
    return [
        {
            "chunk_id": s.get("id", ""),
            "score": round(s.get("similarity", 0), 3),
            "content_preview": s.get("content", "")[:200],
            "doc_title": s.get("doc_title", "Study Material"),
        }
        for s in sources
    ]
