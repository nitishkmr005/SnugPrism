"""Educational standalone: extract and print text from a PDF.

Usage:
    uv run python scripts/ingest_pdf.py path/to/file.pdf
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.pdf_processor import extract

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ingest_pdf.py <path_to_pdf>")
        sys.exit(1)
    content = extract(sys.argv[1])
    print(f"Title: {content.title}")
    print(f"Pages: {len(content.pages)}")
    print(f"Total chars: {len(content.full_text)}")
    print("\n--- First 1000 chars ---")
    print(content.full_text[:1000])
