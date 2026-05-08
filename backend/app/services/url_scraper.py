"""Scrape article text from a URL using httpx + BeautifulSoup4.

Handles bot-blocking (403/429) via multiple User-Agent strategies and
graceful degradation so ingestion never hard-crashes on a blocked page.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from loguru import logger

_ARXIV_ID_RE = re.compile(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)', re.I)

# Full browser headers — Chrome 124 on macOS M2
_CHROME_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xhtml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}

# Mobile UA — some paywalled sites serve lighter versions to mobile
_MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.4 Mobile/15E148 Safari/604.1"
)

_BOT_BLOCKED_MSG = (
    "The site returned {status} (bot protection). "
    "Try pasting the article text directly into the chat, "
    "or use a public mirror / archived version of the URL."
)


@dataclass
class URLContent:
    title: str
    full_text: str
    url: str


async def _try_arxiv(url: str, client: httpx.AsyncClient) -> URLContent | None:
    """Fetch arxiv papers via ar5iv HTML renderer, which is publicly accessible."""
    m = _ARXIV_ID_RE.search(url)
    if not m:
        return None
    arxiv_id = re.sub(r'v\d+$', '', m.group(1))
    ar5iv_url = f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"
    try:
        resp = await client.get(ar5iv_url, headers=_CHROME_HEADERS)
        resp.raise_for_status()
        content = _extract(resp.text, url)
        logger.info(f"arxiv via ar5iv: '{content.title}' ({len(content.full_text)} chars)")
        return content
    except Exception as e:
        logger.warning(f"ar5iv fallback failed for {url}: {e}")
        return None


def _extract(html: str, url: str) -> URLContent:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    title = soup.title.string.strip() if soup.title else urlparse(url).netloc
    container = soup.find("article") or soup.find("main") or soup.find("body")
    text = container.get_text(separator="\n", strip=True) if container else ""
    return URLContent(title=title, full_text=text, url=url)


async def scrape(url: str) -> URLContent:
    """
    Fetch URL and extract main text content.

    Strategy:
    1. Full Chrome desktop headers
    2. On 403/429: retry with mobile User-Agent
    3. On 403/429 again: raise a descriptive ScrapingError
    """
    parsed = urlparse(url)
    base_headers = dict(_CHROME_HEADERS)
    base_headers["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        # Attempt 1 — desktop Chrome
        try:
            resp = await client.get(url, headers=base_headers)
            if resp.status_code not in (403, 429):
                resp.raise_for_status()
                content = _extract(resp.text, url)
                logger.info(f"Scraped '{content.title}' from {url}: {len(content.full_text)} chars")
                return content
        except httpx.HTTPStatusError as e:
            if e.response.status_code not in (403, 429):
                raise
            logger.warning(f"Attempt 1 blocked ({e.response.status_code}) for {url} — retrying with mobile UA")

        # Attempt 2 — mobile Safari
        mobile_headers = {**base_headers, "User-Agent": _MOBILE_UA}
        last_status = 403
        try:
            resp = await client.get(url, headers=mobile_headers)
            if resp.status_code not in (403, 429):
                resp.raise_for_status()
                content = _extract(resp.text, url)
                logger.info(f"Scraped (mobile UA) '{content.title}' from {url}: {len(content.full_text)} chars")
                return content
            last_status = resp.status_code
            logger.warning(f"Attempt 2 also blocked ({last_status}) for {url}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code not in (403, 429):
                raise
            last_status = e.response.status_code
            logger.warning(f"Attempt 2 also blocked ({last_status}) for {url}")

        # Attempt 3 — arxiv-specific fallback via ar5iv HTML renderer
        arxiv_content = await _try_arxiv(url, client)
        if arxiv_content:
            return arxiv_content

        raise ScrapingError(_BOT_BLOCKED_MSG.format(status=last_status), url=url, status=last_status)


class ScrapingError(Exception):
    """Raised when a URL cannot be scraped due to bot-protection or auth."""
    def __init__(self, message: str, url: str, status: int):
        super().__init__(message)
        self.url = url
        self.status = status
