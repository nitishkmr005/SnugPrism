"""Educational standalone: smoke test the RAG pipeline.

Usage:
    uv run python scripts/test_rag.py [query]
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.logging import setup_logging
from config.settings import get_settings

setup_logging()


async def main():
    query = " ".join(sys.argv[1:]) or "Explain the two-tower recommender architecture"
    print(f"Query: {query}\n")

    from app.services.embeddings import embed_one
    vec = await embed_one(query)
    print(f"Embedding dim: {len(vec)}, first 5 values: {vec[:5]}")

    from app.services.db import search_chunks
    results = search_chunks(vec, top_k=3)
    print(f"\nTop {len(results)} chunks:")
    for r in results:
        print(f"  score={r.get('similarity', 0):.3f}: {r.get('content', '')[:120]}...")


if __name__ == "__main__":
    asyncio.run(main())
