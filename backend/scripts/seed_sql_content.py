"""
Seed script: loads SQL Q&As and Learning Hub sections from static JSON files.
Idempotent — skips questions that already exist (duplicate check on question text + topic).

Usage (from backend/):
    uv run python scripts/seed_sql_content.py
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from config.logging import setup_logging
from app.services.document_db import fetch_topics, insert_question, get_db

setup_logging()

DATA_DIR = Path(__file__).parent.parent / "data" / "seed"
QA_FILE = DATA_DIR / "questions.json"
HUB_FILE = DATA_DIR / "sql_hub_sections.json"

SQL_TOPIC_SLUGS = {"sql"}


async def seed_sql_questions(topics_by_slug: dict) -> int:
    questions = json.loads(QA_FILE.read_text())
    sql_qs = [q for q in questions if q.get("topic_slug") in SQL_TOPIC_SLUGS]
    inserted = 0
    for q in sql_qs:
        slug = q.pop("topic_slug")
        topic = topics_by_slug.get(slug)
        if not topic:
            logger.warning(f"Unknown topic slug: {slug}")
            continue
        try:
            await insert_question({
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
            })
            inserted += 1
        except Exception as e:
            logger.warning(f"Skipped (likely duplicate) '{q['question'][:60]}': {e}")
    return inserted


async def seed_sql_hub_sections(topics_by_slug: dict) -> int:
    sections = json.loads(HUB_FILE.read_text())
    topic = topics_by_slug.get("sql")
    if not topic:
        logger.error("Topic 'sql' not found — run the main seed script first")
        return 0

    from bson import ObjectId
    db = get_db()
    existing_count = await db.hub_sections.count_documents({"topic_id": ObjectId(topic["id"])})
    if existing_count > 0:
        logger.info(f"Hub sections for sql already exist ({existing_count}), skipping")
        return 0

    rows = [
        {
            "topic_id": ObjectId(topic["id"]),
            "title": s["title"],
            "content": s["content"],
            "sort_order": s["sort_order"],
            "diagram_def": s.get("diagram_def"),
        }
        for s in sections
    ]
    await db.hub_sections.insert_many(rows)
    logger.success(f"Inserted {len(rows)} hub sections for sql")
    return len(rows)


async def main():
    logger.info("=== Seeding SQL content ===")
    topics = await fetch_topics()
    topics_by_slug = {t["slug"]: t for t in topics}

    if not topics:
        logger.error("No topics found — run 'make seed' first to seed topics")
        return

    qa_count = await seed_sql_questions(topics_by_slug)
    logger.success(f"Q&As: inserted {qa_count} SQL questions")

    hub_count = await seed_sql_hub_sections(topics_by_slug)
    logger.success(f"Hub sections: inserted {hub_count} sections")

    logger.info("=== Done ===")


if __name__ == "__main__":
    asyncio.run(main())
