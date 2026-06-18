from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from config.settings import get_settings
from config.logging import setup_logging
from app.routers import health, topics, questions, hub, chat, ingest, run_summary

setup_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.vector_db import delete_by_doc_id, ensure_collection
    from app.services.document_db import (
        cleanup_duplicate_documents,
        cleanup_duplicate_questions,
        init_indexes,
    )
    await ensure_collection()
    stale_doc_ids = await cleanup_duplicate_documents()
    for doc_id in stale_doc_ids:
        await delete_by_doc_id(doc_id)
    if stale_doc_ids:
        logger.info(f"Removed {len(stale_doc_ids)} duplicate document row(s)")
    stale_qa_count = await cleanup_duplicate_questions()
    if stale_qa_count:
        logger.info(f"Removed {stale_qa_count} duplicate Q&A row(s)")
    await init_indexes()
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(topics.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(hub.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(run_summary.router, prefix="/api")


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.url}: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
