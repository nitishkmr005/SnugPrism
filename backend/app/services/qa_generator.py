"""Orchestrates: extract → chunk → embed → Codex Q&A generation → store."""
from __future__ import annotations
import json
import re
from loguru import logger
from config.settings import get_settings
from app.services import llm, embeddings
from app.services.document_db import (
    fetch_topics,
    insert_document,
    update_document_chunk_count,
    update_document_topic_ids,
    insert_question,
    fetch_topic_by_id,
)
from app.services.vector_db import upsert_chunks
from app.prompts.qa_generation import build_qa_prompt


def _chunk_text(text: str, size: int, overlap: int) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        start += size - overlap
    return [c for c in chunks if c.strip()]


def _parse_qa_json(raw: str) -> list[dict]:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse Q&A JSON: {e}")
        return []


async def detect_topics(text: str) -> list[str]:
    """
    Use the chat LLM to identify which of the 9 study topics a document covers.
    Returns a list of matching topic IDs (MongoDB ObjectId strings).
    """
    all_topics = await fetch_topics()
    if not all_topics:
        return []

    slug_to_id = {t["slug"]: t["id"] for t in all_topics}
    topic_list = ", ".join(f"{t['slug']} ({t['label']})" for t in all_topics)

    messages = [
        {
            "role": "system",
            "content": "You identify which study topics a document covers. Reply only with a valid JSON array of slugs.",
        },
        {
            "role": "user",
            "content": (
                f"Available topics: {topic_list}\n\n"
                f"Document excerpt:\n{text[:2500]}\n\n"
                "Return a JSON array of the slugs that are clearly covered — e.g. [\"sql\", \"llms\"]. "
                "Return [] if none match."
            ),
        },
    ]

    raw = await llm.complete(messages, max_tokens=150, purpose="topic_detection")
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)
    try:
        slugs = json.loads(raw)
        ids = [slug_to_id[s] for s in slugs if s in slug_to_id]
        logger.info(f"Auto-detected topics: {slugs}")
        return ids
    except Exception:
        return []


async def ingest_and_generate(
    title: str,
    source_type: str,
    source_ref: str,
    full_text: str,
    pages: list[dict],
    topic_ids: list[str],
    generate_qa: bool = True,
    doc_id: str | None = None,
) -> tuple[str, int, int]:
    """
    Insert document + chunks, optionally generate Q&A pairs with Codex.
    Returns (doc_id, chunk_count, qa_count).

    If topic_ids is empty, auto-detects topics from document content.
    If doc_id is provided, skips document insertion (already created by router).
    """
    s = get_settings()

    # Auto-detect topics if none provided
    if not topic_ids:
        logger.info("No topics provided — auto-detecting from document content...")
        topic_ids = await detect_topics(full_text)

    if doc_id is None:
        doc = await insert_document(title, source_type, source_ref, topic_ids)
        doc_id = doc["id"]
    elif topic_ids:
        # Update the pre-created document with auto-detected topic_ids
        await update_document_topic_ids(doc_id, topic_ids)

    # Build chunks with page mapping
    chunks: list[str] = []
    page_numbers: list[int | None] = []
    if pages:
        for pg in pages:
            pg_chunks = _chunk_text(pg["text"], s.rag_chunk_size, s.rag_chunk_overlap)
            for c in pg_chunks:
                chunks.append(c)
                page_numbers.append(pg.get("page_number"))
    else:
        chunks = _chunk_text(full_text, s.rag_chunk_size, s.rag_chunk_overlap)
        page_numbers = [None] * len(chunks)

    # Embed in batches of 20
    all_vectors: list[list[float]] = []
    for i in range(0, len(chunks), 20):
        vecs = await embeddings.embed(chunks[i : i + 20])
        all_vectors.extend(vecs)

    # Upsert vectors into Qdrant
    chunk_dicts = [
        {
            "chunk_index": i,
            "content": chunks[i],
            "page_number": page_numbers[i],
            "embedding": all_vectors[i],
            "doc_title": title,
        }
        for i in range(len(chunks))
    ]
    await upsert_chunks(doc_id, chunk_dicts)
    await update_document_chunk_count(doc_id, len(chunks))
    logger.info(f"Inserted {len(chunks)} chunks for doc {doc_id}")

    # Q&A generation using Codex CLI (headless, in background); falls back to direct LLM
    from app.services import codex_runner
    qa_count = 0
    if generate_qa and topic_ids:
        text_for_qa = full_text[:8000]
        for tid in topic_ids:
            topic = await fetch_topic_by_id(tid)
            if not topic:
                continue
            messages = build_qa_prompt(text_for_qa, topic["label"], n=15, document_title=title)
            try:
                combined_prompt = messages[0]["content"] + "\n\n" + messages[1]["content"]
                raw = await codex_runner.run(combined_prompt, purpose="qa_generation")
            except RuntimeError as e:
                logger.warning(f"Codex exec unavailable — falling back to direct LLM: {e}")
                raw = await llm.complete(
                    messages,
                    max_tokens=4000,
                    model=s.qa_model,
                    purpose="qa_generation",
                )
            qa_pairs = _parse_qa_json(raw)
            for pair in qa_pairs:
                try:
                    await insert_question(
                        {
                            "topic_id": tid,
                            "question": pair["question"],
                            "answer": pair["answer"],
                            "difficulty": pair.get("difficulty", "medium"),
                            "tags": pair.get("tags", []),
                            "code_snippet": pair.get("code_snippet"),
                            "comparison_table": pair.get("comparison_table"),
                            "reference_urls": pair.get("reference_urls", []),
                            "pdf_links": [],
                            "source": "generated",
                        }
                    )
                    qa_count += 1
                except Exception as e:
                    logger.warning(f"Failed to insert Q&A pair: {e}")
            logger.info(f"Codex generated {len(qa_pairs)} Q&As for topic {topic['label']}")

    return doc_id, len(chunks), qa_count
