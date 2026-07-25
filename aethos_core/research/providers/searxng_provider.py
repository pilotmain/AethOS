# SPDX-License-Identifier: Apache-2.0
"""SearXNG self-hosted search provider."""

from __future__ import annotations

import logging

import httpx

from aethos_core.research.research_provider import SearchResult, SearchResultSet

_LOG = logging.getLogger("aethos.research.searxng")

_DEFAULT_TIMEOUT_SEC = 25.0


class SearxngResearchProvider:
    def __init__(self, base_url: str, *, timeout_sec: float = _DEFAULT_TIMEOUT_SEC) -> None:
        raw = (base_url or "").strip().rstrip("/")
        self._base_url = raw
        self._timeout = timeout_sec

    def search(self, query: str, *, max_results: int = 5) -> SearchResultSet:
        q = (query or "").strip()
        if not q:
            return SearchResultSet(ok=False, query=q, provider="searxng", detail="Search query is empty.")
        if not self._base_url:
            return SearchResultSet(ok=False, query=q, provider="searxng", detail="SearXNG base URL is missing.")

        capped = min(max(int(max_results), 1), 20)
        url = f"{self._base_url}/search"
        _LOG.info("SearXNG search query=%r max_results=%s base=%s", q[:120], capped, self._base_url)
        try:
            with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
                resp = client.get(
                    url,
                    params={"q": q, "format": "json", "categories": "general"},
                )
        except httpx.TimeoutException:
            return SearchResultSet(ok=False, query=q, provider="searxng", detail="SearXNG search timed out.")
        except httpx.HTTPError as exc:
            return SearchResultSet(
                ok=False,
                query=q,
                provider="searxng",
                detail=f"SearXNG request failed: {exc.__class__.__name__}",
            )

        if resp.status_code >= 400:
            return SearchResultSet(
                ok=False,
                query=q,
                provider="searxng",
                detail=f"SearXNG HTTP {resp.status_code}",
            )

        try:
            data = resp.json()
        except ValueError:
            return SearchResultSet(ok=False, query=q, provider="searxng", detail="SearXNG returned invalid JSON.")

        rows: list[SearchResult] = []
        for item in (data.get("results") or [])[:capped]:
            if not isinstance(item, dict):
                continue
            rows.append(
                SearchResult(
                    title=str(item.get("title") or "Untitled"),
                    url=str(item.get("url") or ""),
                    snippet=str(item.get("content") or item.get("snippet") or "")[:500],
                )
            )
        return SearchResultSet(ok=True, query=q, results=rows, provider="searxng", detail="")
