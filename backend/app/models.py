from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import BaseModel


class TopicOut(BaseModel):
    id: str
    slug: str
    label: str
    sort_order: int


class PDFLink(BaseModel):
    doc_id: str
    page: int
    label: str


class ComparisonTable(BaseModel):
    headers: list[str]
    rows: list[list[str]]


class QuestionOut(BaseModel):
    id: str
    topic: TopicOut
    question: str
    answer: str
    difficulty: str
    tags: list[str]
    code_snippet: str | None
    comparison_table: ComparisonTable | None
    reference_urls: list[str]
    pdf_links: list[PDFLink]
    source: str
    created_at: datetime


class QuestionCreate(BaseModel):
    topic_id: str
    question: str
    answer: str
    difficulty: str
    tags: list[str] = []
    code_snippet: str | None = None
    comparison_table: dict[str, Any] | None = None
    reference_urls: list[str] = []
    pdf_links: list[dict[str, Any]] = []


class QuestionUpdate(BaseModel):
    topic_id: str | None = None
    question: str | None = None
    answer: str | None = None
    difficulty: str | None = None
    tags: list[str] | None = None
    code_snippet: str | None = None
    comparison_table: dict[str, Any] | None = None
    reference_urls: list[str] | None = None
    pdf_links: list[dict[str, Any]] | None = None


class QuestionsPage(BaseModel):
    items: list[QuestionOut]
    total: int


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    stream: bool = False
    include_web_search: bool = True
    format: str = "markdown"  # "markdown" | "text"


class SourceChunk(BaseModel):
    chunk_id: str
    score: float
    content_preview: str
    doc_title: str


class ArticleResult(BaseModel):
    title: str
    url: str
    snippet: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    sources: list[SourceChunk]
    articles: list[ArticleResult]


class IngestUrlRequest(BaseModel):
    url: str
    topic_ids: list[str]
    generate_qa: bool = True


class IngestStatusResponse(BaseModel):
    doc_id: str
    status: str  # "processing" | "done" | "failed"
    chunk_count: int
    qa_count: int
    error: str | None = None


class DocumentOut(BaseModel):
    id: str
    title: str
    source_type: str
    source_ref: str
    topic_ids: list[str]
    chunk_count: int
    ingested_at: datetime


class HubSection(BaseModel):
    id: str
    title: str
    content: str
    sort_order: int
    diagram_def: str | None


class HubResponse(BaseModel):
    topic: TopicOut
    sections: list[HubSection]
    documents: list[DocumentOut] = []
