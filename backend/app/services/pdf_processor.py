"""Extract text and page-level content from PDF files using pdfplumber."""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
import pdfplumber
from loguru import logger


@dataclass
class PageContent:
    page_number: int
    text: str


@dataclass
class PDFContent:
    title: str
    full_text: str
    pages: list[PageContent]


def extract(pdf_path: str | Path) -> PDFContent:
    """Extract text from a PDF, returning full text and per-page content."""
    path = Path(pdf_path)
    pages: list[PageContent] = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append(PageContent(page_number=i, text=text))
    full_text = "\n\n".join(p.text for p in pages if p.text.strip())
    logger.info(f"Extracted {len(pages)} pages from {path.name}, {len(full_text)} chars")
    return PDFContent(title=path.stem.replace("_", " "), full_text=full_text, pages=pages)
