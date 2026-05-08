"""Tavily web search wrapper. Returns empty list on any failure."""
from __future__ import annotations
from loguru import logger
from config.settings import get_settings


async def search(query: str, max_results: int | None = None) -> list[dict]:
    """Search the web. Returns [{title, url, snippet}]."""
    s = get_settings()
    if not s.tavily_api_key:
        logger.warning("TAVILY_API_KEY not set; skipping web search")
        return []
    n = max_results or s.web_search_max_results
    try:
        from tavily import AsyncTavilyClient
        client = AsyncTavilyClient(api_key=s.tavily_api_key)
        resp = await client.search(query, max_results=n, search_depth="basic")
        results = [
            {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
            for r in resp.get("results", [])
        ]
        logger.info(f"Web search '{query[:40]}': {len(results)} results")
        return results
    except Exception as exc:
        logger.warning(f"Web search failed: {exc}")
        return []
