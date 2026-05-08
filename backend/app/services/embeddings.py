"""Provider-agnostic embedding layer.

Providers:
  local   — sentence-transformers (BAAI/bge-m3, 1024-dim, SOTA on MTEB retrieval)
  openai  — OpenAI embeddings API (text-embedding-3-small, 1536-dim)
"""
from __future__ import annotations
import asyncio
from loguru import logger
from config.settings import get_settings

# Module-level singleton — avoids reloading the model on every call (~2GB, slow to load)
_local_model = None


def _get_local_model():
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer
        import torch
        if torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"
        s = get_settings()
        logger.info(f"Loading embedding model '{s.embedding_model}' on {device} (first load may take ~30s)")
        _local_model = SentenceTransformer(s.embedding_model, device=device)
        logger.info("Embedding model ready")
    return _local_model


async def embed(texts: list[str]) -> list[list[float]]:
    s = get_settings()
    if s.embedding_provider == "local":
        return await _embed_local(texts)
    if s.embedding_provider == "openai":
        return await _embed_openai(texts)
    raise ValueError(f"Unsupported embedding_provider: {s.embedding_provider}")


async def embed_one(text: str) -> list[float]:
    return (await embed([text]))[0]


async def _embed_local(texts: list[str]) -> list[list[float]]:
    model = _get_local_model()
    loop = asyncio.get_event_loop()
    # Run in thread pool — encode() is CPU-bound and would block the event loop
    vectors: list[list[float]] = await loop.run_in_executor(
        None,
        lambda: model.encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist(),
    )
    logger.debug(f"Embedded {len(texts)} texts locally → {len(vectors[0])}-dim")
    return vectors


async def _embed_openai(texts: list[str]) -> list[list[float]]:
    from openai import AsyncOpenAI
    from app.services.run_logger import log_run
    s = get_settings()
    client = AsyncOpenAI(api_key=s.openai_api_key)
    resp = await client.embeddings.create(model=s.embedding_model, input=texts)
    vectors = [item.embedding for item in sorted(resp.data, key=lambda x: x.index)]
    if resp.usage:
        await log_run("embedding", s.embedding_model, "embedding", resp.usage.total_tokens)
        logger.debug(f"Embedded {len(texts)} texts (openai) → {len(vectors[0])}-dim ({resp.usage.total_tokens} tokens)")
    return vectors
