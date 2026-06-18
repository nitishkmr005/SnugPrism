"""Rebuild Qdrant vectors from documents already present in MongoDB."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from app.services import qa_generator
from app.services.document_db import cleanup_duplicate_documents, fetch_documents, init_indexes
from app.services.pdf_processor import extract as pdf_extract
from app.services.url_scraper import ScrapingError, scrape
from app.services.vector_db import delete_by_doc_id, ensure_collection
from config.settings import get_settings


async def reindex() -> None:
    await ensure_collection()

    stale_doc_ids = await cleanup_duplicate_documents()
    for doc_id in stale_doc_ids:
        await delete_by_doc_id(doc_id)
    await init_indexes()

    settings = get_settings()
    docs = await fetch_documents()
    logger.info(f"Reindexing {len(docs)} document(s)")

    for doc in docs:
        doc_id = doc["id"]
        await delete_by_doc_id(doc_id)

        try:
            if doc["source_type"] == "pdf":
                pdf_path = settings.pdfs_dir / doc["source_ref"]
                if not pdf_path.exists():
                    logger.warning(f"Skipping missing PDF for {doc_id}: {pdf_path}")
                    continue
                content = pdf_extract(pdf_path)
                pages = [{"page_number": p.page_number, "text": p.text} for p in content.pages]
                full_text = content.full_text
                title = content.title or doc["title"]
            elif doc["source_type"] == "url":
                content = await scrape(doc["source_ref"])
                pages = []
                full_text = content.full_text
                title = content.title or doc["title"]
            else:
                logger.warning(f"Skipping unsupported source type for {doc_id}: {doc['source_type']}")
                continue

            _, chunk_count, _ = await qa_generator.ingest_and_generate(
                title=title,
                source_type=doc["source_type"],
                source_ref=doc["source_ref"],
                full_text=full_text,
                pages=pages,
                topic_ids=doc.get("topic_ids") or [],
                generate_qa=False,
                doc_id=doc_id,
            )
            logger.info(f"Reindexed {doc_id}: {chunk_count} chunk(s)")
        except ScrapingError as exc:
            logger.warning(f"Skipping URL {doc['source_ref']}: {exc}")
        except Exception as exc:
            logger.exception(f"Failed to reindex {doc_id}: {exc}")


if __name__ == "__main__":
    asyncio.run(reindex())
