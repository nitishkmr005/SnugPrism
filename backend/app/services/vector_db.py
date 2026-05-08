"""Qdrant vector store. Handles chunk embeddings and similarity search."""
from __future__ import annotations
import uuid
from loguru import logger
from qdrant_client import AsyncQdrantClient, models
from config.settings import get_settings

_client: AsyncQdrantClient | None = None


def get_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        s = get_settings()
        if s.qdrant_url:
            _client = AsyncQdrantClient(url=s.qdrant_url, api_key=s.qdrant_api_key)
        else:
            _client = AsyncQdrantClient(host=s.qdrant_host, port=s.qdrant_port)
    return _client


async def ensure_collection() -> None:
    """Create the chunks collection if it doesn't exist, or recreate if dimension changed."""
    s = get_settings()
    client = get_client()
    existing = await client.get_collections()
    names = {c.name for c in existing.collections}

    if s.qdrant_collection in names:
        info = await client.get_collection(s.qdrant_collection)
        vp = info.config.params.vectors
        existing_dim = vp.size if hasattr(vp, "size") else None
        if existing_dim == s.embedding_dimension:
            return  # Already correct
        logger.warning(
            f"Qdrant collection dimension mismatch: existing={existing_dim}, "
            f"configured={s.embedding_dimension}. Recreating — re-ingest documents to rebuild vectors."
        )
        await client.delete_collection(s.qdrant_collection)

    await client.create_collection(
        collection_name=s.qdrant_collection,
        vectors_config=models.VectorParams(
            size=s.embedding_dimension,
            distance=models.Distance.COSINE,
        ),
    )
    logger.info(f"Created Qdrant collection: {s.qdrant_collection} ({s.embedding_dimension}-dim)")


async def upsert_chunks(doc_id: str, chunks: list[dict]) -> list[str]:
    """
    Upsert chunk embeddings into Qdrant. Returns list of assigned point IDs.

    Each chunk dict: {chunk_index, content, page_number, embedding, doc_title}
    """
    s = get_settings()
    points = []
    point_ids: list[str] = []
    for chunk in chunks:
        pid = str(uuid.uuid4())
        point_ids.append(pid)
        points.append(
            models.PointStruct(
                id=pid,
                vector=chunk["embedding"],
                payload={
                    "doc_id": doc_id,
                    "chunk_index": chunk["chunk_index"],
                    "content": chunk["content"],
                    "page_number": chunk.get("page_number"),
                    "doc_title": chunk.get("doc_title", "Study Material"),
                },
            )
        )
    await get_client().upsert(collection_name=s.qdrant_collection, points=points)
    logger.debug(f"Upserted {len(points)} chunks for doc {doc_id}")
    return point_ids


async def search_chunks(query_embedding: list[float], top_k: int = 5) -> list[dict]:
    """Cosine similarity search. Returns list of chunk dicts with score."""
    s = get_settings()
    results = await get_client().search(
        collection_name=s.qdrant_collection,
        query_vector=query_embedding,
        limit=top_k,
        with_payload=True,
    )
    return [
        {
            "id": str(r.id),
            "similarity": r.score,
            "content": r.payload.get("content", "") if r.payload else "",
            "doc_title": r.payload.get("doc_title", "Study Material") if r.payload else "Study Material",
            "doc_id": r.payload.get("doc_id") if r.payload else None,
            "page_number": r.payload.get("page_number") if r.payload else None,
        }
        for r in results
    ]


async def fetch_chunks_by_page(doc_id: str, page_num: int) -> list[str]:
    """Return chunk text for a specific document page from Qdrant payload."""
    s = get_settings()
    results, _ = await get_client().scroll(
        collection_name=s.qdrant_collection,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id)),
                models.FieldCondition(key="page_number", match=models.MatchValue(value=page_num)),
            ]
        ),
        with_payload=True,
        limit=100,
    )
    return [r.payload.get("content", "") for r in results if r.payload]


async def delete_by_doc_id(doc_id: str) -> None:
    """Delete all Qdrant points associated with a document."""
    s = get_settings()
    await get_client().delete(
        collection_name=s.qdrant_collection,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="doc_id",
                        match=models.MatchValue(value=doc_id),
                    )
                ]
            )
        ),
    )
