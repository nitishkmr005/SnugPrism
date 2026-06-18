"""
Seed script: loads Q&As for statistics, ml_models, llms, ai_agents, llm_inferencing,
and recommender_systems from questions.json into MongoDB.
Idempotent — skips questions that already exist.

Usage (from backend/):
    uv run python scripts/seed_remaining_topics_content.py
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from config.logging import setup_logging
from app.services.document_db import fetch_topics, insert_question

setup_logging()

DATA_DIR = Path(__file__).parent.parent / "data" / "seed"
QA_FILE = DATA_DIR / "questions.json"

TARGET_SLUGS = {
    "statistics",
    "ml_models",
    "llms",
    "ai_agents",
    "llm_inferencing",
    "recommender_systems",
}


async def main():
    logger.info("=== Seeding remaining topic Q&As ===")
    topics = await fetch_topics()
    topics_by_slug = {t["slug"]: t for t in topics}

    if not topics:
        logger.error("No topics found — run 'make seed' first")
        return

    questions = json.loads(QA_FILE.read_text())
    target_qs = [q for q in questions if q.get("topic_slug") in TARGET_SLUGS]
    logger.info(f"Found {len(target_qs)} questions across target topics")

    counts: dict[str, int] = {}
    for q in target_qs:
        slug = q["topic_slug"]
        topic = topics_by_slug.get(slug)
        if not topic:
            logger.warning(f"Topic slug '{slug}' not found in DB — skipping")
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
            counts[slug] = counts.get(slug, 0) + 1
        except Exception as e:
            logger.warning(f"Skipped (duplicate) '{q['question'][:60]}': {e}")

    for slug, n in sorted(counts.items()):
        logger.success(f"  {slug}: inserted {n}")
    logger.success(f"Total inserted: {sum(counts.values())}")
    logger.info("=== Done ===")


if __name__ == "__main__":
    asyncio.run(main())
