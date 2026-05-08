import shutil
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from app.models import IngestUrlRequest, IngestStatusResponse, DocumentOut
from app.services import qa_generator
from app.services.document_db import fetch_documents, insert_document
from app.services.vector_db import fetch_chunks_by_page
from app.services.pdf_processor import extract as pdf_extract
from app.services.url_scraper import scrape, ScrapingError
from config.settings import get_settings
from loguru import logger

router = APIRouter()

_status: dict[str, dict] = {}


def _set_status(doc_id: str, status: str, chunk_count: int = 0, qa_count: int = 0, error: str | None = None):
    _status[doc_id] = {"status": status, "chunk_count": chunk_count, "qa_count": qa_count, "error": error}


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

    # topic_ids may be empty — auto-detect runs in background if so
    ids = [i.strip() for i in topic_ids.split(",") if i.strip()]
    doc = await insert_document(file.filename, "pdf", file.filename, ids)
    doc_id = doc["id"]
    _set_status(doc_id, "processing")

    background_tasks.add_task(_process_pdf, doc_id, pdf_path, ids, generate_qa)
    return {"doc_id": doc_id, "status": "processing"}


@router.post("/ingest/url")
async def ingest_url(background_tasks: BackgroundTasks, body: IngestUrlRequest):
    doc = await insert_document(body.url, "url", body.url, body.topic_ids)
    doc_id = doc["id"]
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


@router.get("/documents/{doc_id}/page/{page_num}")
async def get_document_page(doc_id: str, page_num: int):
    contents = await fetch_chunks_by_page(doc_id, page_num)
    if not contents:
        raise HTTPException(404, "Page not found")
    return {"doc_id": doc_id, "page_num": page_num, "content": "\n".join(contents)}
