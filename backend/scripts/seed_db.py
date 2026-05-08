"""
Seed script: loads bootstrap Q&As from data/seed/questions.json,
then ingests the resume PDF and generates GPT-4o Q&As + Hub content.

Usage (from backend/):
    uv run python scripts/seed_db.py [--skip-pdf] [--skip-hub]
"""
import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from config.settings import get_settings
from config.logging import setup_logging
from app.services.document_db import (
    fetch_topics,
    fetch_topic_by_slug,
    insert_topic,
    insert_question,
    insert_hub_sections_batch,
)
from app.services.vector_db import ensure_collection
from app.services import llm
from app.services.pdf_processor import extract as pdf_extract
from app.services.qa_generator import ingest_and_generate
from app.prompts.qa_generation import build_hub_prompt

setup_logging()
settings = get_settings()

TOPICS = [
    {"slug": "sql", "label": "SQL", "sort_order": 1},
    {"slug": "statistics", "label": "Statistics", "sort_order": 2},
    {"slug": "ml_models", "label": "ML Models", "sort_order": 3},
    {"slug": "recommender_systems", "label": "Recommender Systems", "sort_order": 4},
    {"slug": "llms", "label": "LLMs", "sort_order": 5},
    {"slug": "ai_agents", "label": "AI Agents", "sort_order": 6},
    {"slug": "embedding_models", "label": "Embedding Models", "sort_order": 7},
    {"slug": "llm_inferencing", "label": "LLM Inferencing", "sort_order": 8},
    {"slug": "evaluation", "label": "Evaluation", "sort_order": 9},
]


async def seed_topics():
    existing = {t["slug"] for t in await fetch_topics()}
    new_topics = [t for t in TOPICS if t["slug"] not in existing]
    for t in new_topics:
        await insert_topic(t)
    if new_topics:
        logger.info(f"Inserted {len(new_topics)} topics")
    else:
        logger.info("Topics already seeded")


async def seed_bootstrap_questions():
    seed_file = Path(__file__).parent.parent / "data" / "seed" / "questions.json"
    questions = json.loads(seed_file.read_text())
    topics = {t["slug"]: t for t in await fetch_topics()}

    inserted = 0
    for q in questions:
        slug = q.pop("topic_slug")
        topic = topics.get(slug)
        if not topic:
            logger.warning(f"Unknown topic slug: {slug}")
            continue
        try:
            await insert_question(
                {
                    "topic_id": topic["id"],
                    "question": q["question"],
                    "answer": q["answer"],
                    "difficulty": q.get("difficulty", "medium"),
                    "tags": q.get("tags", []),
                    "code_snippet": q.get("code_snippet"),
                    "comparison_table": q.get("comparison_table"),
                    "reference_urls": q.get("reference_urls", []),
                    "pdf_links": [],
                    "source": "seeded",
                }
            )
            inserted += 1
        except Exception as e:
            logger.warning(f"Skipped question '{q['question'][:50]}': {e}")

    logger.success(f"Seeded {inserted}/{len(questions)} bootstrap questions")


async def seed_from_resume():
    resume_path = Path(__file__).parent.parent.parent.parent / "resume" / "NitishHarsoorResume_2026.pdf"
    if not resume_path.exists():
        logger.warning(f"Resume not found at {resume_path}; skipping resume ingestion")
        return

    content = pdf_extract(resume_path)
    topics = await fetch_topics()
    topic_ids = [t["id"] for t in topics]

    logger.info(f"Ingesting resume: {len(content.full_text)} chars across {len(content.pages)} pages")
    pages = [{"page_number": p.page_number, "text": p.text} for p in content.pages]
    doc_id, chunk_count, qa_count = await ingest_and_generate(
        title="Nitish Harsoor Resume 2026",
        source_type="pdf",
        source_ref="NitishHarsoorResume_2026.pdf",
        full_text=content.full_text,
        pages=pages,
        topic_ids=topic_ids,
        generate_qa=True,
    )
    logger.success(f"Resume ingested: {chunk_count} chunks, {qa_count} Q&As generated (doc_id={doc_id})")


async def seed_hub_content():
    topics = await fetch_topics()
    for topic in topics:
        messages = build_hub_prompt(topic["label"], n_sections=6)
        logger.info(f"Generating Hub content for {topic['label']}...")
        raw = await llm.complete(messages, max_tokens=3000)
        raw = raw.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        try:
            sections = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse hub sections for {topic['label']}: {e}")
            continue

        rows = [
            {
                "topic_id": topic["id"],
                "title": s.get("title", ""),
                "content": s.get("content", ""),
                "sort_order": s.get("sort_order", i),
                "diagram_def": s.get("diagram_def"),
            }
            for i, s in enumerate(sections)
        ]
        await insert_hub_sections_batch(rows)
        logger.success(f"Inserted {len(rows)} Hub sections for {topic['label']}")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-pdf", action="store_true")
    parser.add_argument("--skip-hub", action="store_true")
    parser.add_argument("--topics-only", action="store_true")
    args = parser.parse_args()

    logger.info("=== SnugPrism Seed Script ===")
    await ensure_collection()
    await seed_topics()

    if args.topics_only:
        return

    await seed_bootstrap_questions()

    if not args.skip_pdf:
        await seed_from_resume()

    if not args.skip_hub:
        await seed_hub_content()

    logger.success("=== Seeding complete ===")


if __name__ == "__main__":
    asyncio.run(main())
