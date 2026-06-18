"""Regenerate interview Q&As for ingested documents without touching Qdrant vectors."""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from app.services import qa_generator
from app.services.document_db import fetch_documents
from app.services.pdf_processor import extract as pdf_extract
from app.services.url_scraper import ScrapingError, scrape
from config.settings import get_settings


async def regenerate(include_urls: bool, include_pdfs: bool) -> None:
    settings = get_settings()
    docs = await fetch_documents()
    total = 0

    for doc in docs:
        if doc["source_type"] == "pdf" and not include_pdfs:
            continue
        if doc["source_type"] == "url" and not include_urls:
            continue

        try:
            if doc["source_type"] == "pdf":
                pdf_path = settings.pdfs_dir / doc["source_ref"]
                if not pdf_path.exists():
                    logger.warning(f"Skipping missing PDF for {doc['id']}: {pdf_path}")
                    continue
                content = pdf_extract(pdf_path)
                pages = [{"page_number": p.page_number, "text": p.text} for p in content.pages]
                title = content.title or doc["title"]
                full_text = content.full_text
            elif doc["source_type"] == "url":
                content = await scrape(doc["source_ref"])
                pages = []
                title = content.title or doc["title"]
                full_text = content.full_text
            else:
                logger.warning(f"Skipping unsupported source type for {doc['id']}: {doc['source_type']}")
                continue

            count = await qa_generator.generate_qas_for_content(
                doc_id=doc["id"],
                title=title,
                source_type=doc["source_type"],
                source_ref=doc["source_ref"],
                full_text=full_text,
                pages=pages,
                topic_ids=doc.get("topic_ids") or [],
                replace_existing=True,
            )
            total += count
            logger.info(f"Generated {count} Q&As for {doc['source_type']} {doc['source_ref']}")
        except ScrapingError as exc:
            logger.warning(f"Skipping URL {doc['source_ref']}: {exc}")
        except Exception as exc:
            logger.exception(f"Failed to regenerate Q&As for {doc['id']}: {exc}")

    logger.info(f"Generated {total} Q&As total")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-only", action="store_true")
    parser.add_argument("--url-only", action="store_true")
    args = parser.parse_args()

    asyncio.run(
        regenerate(
            include_urls=not args.pdf_only,
            include_pdfs=not args.url_only,
        )
    )
