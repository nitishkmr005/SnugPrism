import shutil
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from app.models import IngestUrlRequest, IngestStatusResponse, DocumentOut
from app.services import qa_generator
from app.services.document_db import (
    fetch_documents,
    fetch_document_by_id,
    fetch_document_by_source_ref,
    insert_document,
    update_document_chunk_count,
    update_document_topic_ids,
)
from app.services.vector_db import fetch_chunks_by_page, delete_by_doc_id
from app.services.pdf_processor import extract as pdf_extract
from app.services.url_scraper import scrape, ScrapingError
from config.settings import get_settings
from loguru import logger

router = APIRouter()

_status: dict[str, dict] = {}


def _set_status(doc_id: str, status: str, chunk_count: int = 0, qa_count: int = 0, error: str | None = None):
    _status[doc_id] = {"status": status, "chunk_count": chunk_count, "qa_count": qa_count, "error": error}


async def _upsert_document(title: str, source_type: str, source_ref: str, topic_ids: list[str]) -> str:
    """Insert or reset an existing document with the same source_ref. Returns doc_id."""
    existing = await fetch_document_by_source_ref(source_ref)
    if existing:
        doc_id = existing["id"]
        await delete_by_doc_id(doc_id)          # clear stale Qdrant vectors
        await update_document_chunk_count(doc_id, 0)
        if topic_ids:
            await update_document_topic_ids(doc_id, topic_ids)
        logger.info(f"Re-ingesting existing document {doc_id} ({source_ref})")
        return doc_id
    doc = await insert_document(title, source_type, source_ref, topic_ids)
    return doc["id"]


async def _process_pdf(doc_id: str, pdf_path: Path, topic_ids: list[str], generate_qa: bool):
    try:
        content = pdf_extract(pdf_path)
        pages = [{"page_number": p.page_number, "text": p.text} for p in content.pages]
        _, chunk_count, qa_count = await qa_generator.ingest_and_generate(
            title=content.title,
            source_type="pdf",
            source_ref=pdf_path.name,
            full_text=content.full_text,
            pages=pages,
            topic_ids=topic_ids,
            generate_qa=generate_qa,
            doc_id=doc_id,
        )
        _set_status(doc_id, "done", chunk_count, qa_count)
    except Exception as e:
        logger.exception(f"PDF ingest failed for {doc_id}: {e}")
        _set_status(doc_id, "failed", error=str(e))


async def _process_url(doc_id: str, url: str, topic_ids: list[str], generate_qa: bool):
    try:
        content = await scrape(url)
        _, chunk_count, qa_count = await qa_generator.ingest_and_generate(
            title=content.title,
            source_type="url",
            source_ref=url,
            full_text=content.full_text,
            pages=[],
            topic_ids=topic_ids,
            generate_qa=generate_qa,
            doc_id=doc_id,
        )
        _set_status(doc_id, "done", chunk_count, qa_count)
    except ScrapingError as e:
        logger.warning(f"Scraping blocked for {doc_id}: {e}")
        _set_status(doc_id, "failed", error=str(e))
    except Exception as e:
        logger.exception(f"URL ingest failed for {doc_id}: {e}")
        _set_status(doc_id, "failed", error=str(e))


async def _regenerate_qas(doc_id: str):
    try:
        doc = await fetch_document_by_id(doc_id)
        if not doc:
            _set_status(doc_id, "failed", error="Document not found")
            return

        if doc["source_type"] == "pdf":
            pdf_path = get_settings().pdfs_dir / doc["source_ref"]
            if not pdf_path.exists():
                _set_status(doc_id, "failed", error="PDF file not found on server")
                return
            content = pdf_extract(pdf_path)
            pages = [{"page_number": p.page_number, "text": p.text} for p in content.pages]
            qa_count = await qa_generator.generate_qas_for_content(
                doc_id=doc_id,
                title=content.title or doc["title"],
                source_type="pdf",
                source_ref=doc["source_ref"],
                full_text=content.full_text,
                pages=pages,
                topic_ids=doc.get("topic_ids") or [],
            )
        elif doc["source_type"] == "url":
            content = await scrape(doc["source_ref"])
            qa_count = await qa_generator.generate_qas_for_content(
                doc_id=doc_id,
                title=content.title or doc["title"],
                source_type="url",
                source_ref=doc["source_ref"],
                full_text=content.full_text,
                pages=[],
                topic_ids=doc.get("topic_ids") or [],
            )
        else:
            _set_status(doc_id, "failed", error=f"Unsupported source type: {doc['source_type']}")
            return

        _set_status(doc_id, "done", doc.get("chunk_count") or 0, qa_count)
    except ScrapingError as e:
        logger.warning(f"Q&A regeneration blocked for {doc_id}: {e}")
        _set_status(doc_id, "failed", error=str(e))
    except Exception as e:
        logger.exception(f"Q&A regeneration failed for {doc_id}: {e}")
        _set_status(doc_id, "failed", error=str(e))


@router.post("/ingest/pdf")
async def ingest_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    topic_ids: str = Form(default=""),
    generate_qa: bool = Form(True),
):
    s = get_settings()
    s.pdfs_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = s.pdfs_dir / file.filename
    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    ids = [i.strip() for i in topic_ids.split(",") if i.strip()]
    doc_id = await _upsert_document(file.filename, "pdf", file.filename, ids)
    _set_status(doc_id, "processing")
    background_tasks.add_task(_process_pdf, doc_id, pdf_path, ids, generate_qa)
    return {"doc_id": doc_id, "status": "processing"}


@router.post("/ingest/url")
async def ingest_url(background_tasks: BackgroundTasks, body: IngestUrlRequest):
    doc_id = await _upsert_document(body.url, "url", body.url, body.topic_ids)
    _set_status(doc_id, "processing")
    background_tasks.add_task(_process_url, doc_id, body.url, body.topic_ids, body.generate_qa)
    return {"doc_id": doc_id, "status": "processing"}


@router.get("/ingest/status/{doc_id}", response_model=IngestStatusResponse)
def ingest_status(doc_id: str):
    s = _status.get(doc_id)
    if not s:
        raise HTTPException(404, "Document not found")
    return IngestStatusResponse(doc_id=doc_id, **s)


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents():
    return await fetch_documents()


@router.get("/documents/{doc_id}/pdf")
async def get_document_pdf(doc_id: str):
    """Serve the raw PDF file so the browser can display it natively."""
    doc = await fetch_document_by_id(doc_id)
    if not doc or doc["source_type"] != "pdf":
        raise HTTPException(404, "PDF document not found")
    pdf_path = get_settings().pdfs_dir / doc["source_ref"]
    if not pdf_path.exists():
        raise HTTPException(404, "PDF file not found on server")
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=doc["source_ref"],
        content_disposition_type="inline",
    )


@router.post("/documents/{doc_id}/regenerate-qas")
async def regenerate_document_qas(doc_id: str, background_tasks: BackgroundTasks):
    doc = await fetch_document_by_id(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    _set_status(doc_id, "processing")
    background_tasks.add_task(_regenerate_qas, doc_id)
    return {"doc_id": doc_id, "status": "processing"}


@router.get("/documents/{doc_id}/page/{page_num}")
async def get_document_page(doc_id: str, page_num: int):
    contents = await fetch_chunks_by_page(doc_id, page_num)
    if not contents:
        raise HTTPException(404, "Page not found")
    return {"doc_id": doc_id, "page_num": page_num, "content": "\n".join(contents)}
