"""Search tools — live web research integration.

This module provides:
- DuckDuckGo HTML search (no API key required)
- Optional page fetching + text extraction (for citations / summaries)
- Lightweight competitor outline extraction

Design goals:
- Work out-of-the-box (no paid API keys)
- Fail gracefully (timeouts, blocks, no-network)
- Keep results structured and easy for agents to cite
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

from app.config import (
    ENABLE_WEB_RESEARCH,
    WEB_RESEARCH_MAX_RESULTS,
    WEB_RESEARCH_FETCH_TOP_N,
    WEB_RESEARCH_MAX_CHARS_PER_SOURCE,
    WEB_RESEARCH_TIMEOUT_SECONDS,
    WEB_RESEARCH_USER_AGENT,
)

logger = logging.getLogger("briefengine")


@dataclass
class WebResult:
    title: str
    url: str
    snippet: str = ""
    source: str = "duckduckgo"


def _clean_text(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "")).strip()
    return s


def _is_http_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https")
    except Exception:
        return False


def search_web(query: str, num_results: int | None = None) -> list[dict]:
    """Perform a lightweight web search.

    Notes:
    - Uses DuckDuckGo's HTML endpoint (no API key).
    - Returns structured results: title, snippet, url.
    - If web research is disabled, returns [].
    """
    if not ENABLE_WEB_RESEARCH:
        logger.info(f"[Search] Web research disabled. Query='{query}'")
        return []

    n = int(num_results or WEB_RESEARCH_MAX_RESULTS)
    n = max(1, min(n, 10))

    try:
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {"User-Agent": WEB_RESEARCH_USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=WEB_RESEARCH_TIMEOUT_SECONDS)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        results: list[WebResult] = []

        # DuckDuckGo HTML: results often in div.result
        for result_div in soup.select("div.result"):
            a = result_div.select_one("a.result__a")
            if not a or not a.get("href"):
                continue
            title = _clean_text(a.get_text(" "))
            href = a.get("href", "").strip()

            # Snippet
            snippet_el = result_div.select_one(".result__snippet")
            snippet = _clean_text(snippet_el.get_text(" ") if snippet_el else "")

            if _is_http_url(href):
                results.append(WebResult(title=title, url=href, snippet=snippet))
            if len(results) >= n:
                break

        # Fallback selector (DDG changes occasionally)
        if not results:
            for a in soup.select("a.result-link"):
                href = (a.get("href") or "").strip()
                title = _clean_text(a.get_text(" "))
                if _is_http_url(href):
                    results.append(WebResult(title=title, url=href, snippet=""))
                if len(results) >= n:
                    break

        # Dedupe by hostname+path
        deduped: list[WebResult] = []
        seen: set[str] = set()
        for r in results:
            key = (urlparse(r.url).netloc + urlparse(r.url).path).lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)

        logger.info(f"[Search] '{query}' -> {len(deduped)} results")
        return [r.__dict__ for r in deduped]

    except Exception as e:
        logger.warning(f"[Search] Web search failed for '{query}': {e}")
        return []


def fetch_url_text(url: str, max_chars: int | None = None) -> str:
    """Fetch a URL and return readable text extracted from HTML.

    - Removes script/style/nav/footer elements.
    - Returns a truncated string (max_chars).
    """
    if not ENABLE_WEB_RESEARCH:
        return ""

    if not _is_http_url(url):
        return ""

    limit = int(max_chars or WEB_RESEARCH_MAX_CHARS_PER_SOURCE)

    try:
        headers = {"User-Agent": WEB_RESEARCH_USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=WEB_RESEARCH_TIMEOUT_SECONDS)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
            tag.decompose()

        text = soup.get_text(" ")
        text = _clean_text(text)

        if len(text) > limit:
            text = text[:limit] + "…"
        return text
    except Exception as e:
        logger.warning(f"[Search] Fetch failed for {url}: {e}")
        return ""


def build_source_pack(query: str) -> dict:
    """Search the web and fetch text for top sources.

    Returns:
    {
      "query": "...",
      "results": [{"title","url","snippet","source"}],
      "top_sources": [{"title","url","snippet","source","extracted_text"}]
    }
    """
    results = search_web(query, WEB_RESEARCH_MAX_RESULTS)
    top_n = max(0, min(WEB_RESEARCH_FETCH_TOP_N, len(results)))
    top_sources = []
    for r in results[:top_n]:
        extracted = fetch_url_text(r.get("url", ""))
        top_sources.append({**r, "extracted_text": extracted})
    return {"query": query, "results": results, "top_sources": top_sources}


def search_competitors(keyword: str) -> list[dict]:
    """Basic competitor scan: returns top result URLs & titles.

    This intentionally avoids scraping full competitor pages by default.
    """
    pack = build_source_pack(keyword)
    return pack.get("results", [])
