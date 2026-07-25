# SPDX-License-Identifier: Apache-2.0
"""Tavily web search provider."""

from __future__ import annotations

import logging

import httpx

from aethos_core.research.research_provider import SearchResult, SearchResultSet

_LOG = logging.getLogger("aethos.research.tavily")

_TAVILY_SEARCH_URL = "https://api.tavily.com/search"
_DEFAULT_TIMEOUT_SEC = 25.0


class TavilyResearchProvider:
    def __init__(self, api_key: str, *, timeout_sec: float = _DEFAULT_TIMEOUT_SEC) -> None:
        self._api_key = (api_key or "").strip()
        self._timeout = timeout_sec

    def search(self, query: str, *, max_results: int = 5) -> SearchResultSet:
        q = (query or "").strip()
        if not q:
            return SearchResultSet(ok=False, query=q, provider="tavily", detail="Search query is empty.")
        if not self._api_key:
            return SearchResultSet(ok=False, query=q, provider="tavily", detail="Tavily API key is missing.")

        capped = min(max(int(max_results), 1), 20)
        _LOG.info("Tavily search query=%r max_results=%s", q[:120], capped)
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(
                    _TAVILY_SEARCH_URL,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self._api_key}",
                    },
                    json={"query": q, "max_results": capped},
                )
        except httpx.TimeoutException:
            return SearchResultSet(ok=False, query=q, provider="tavily", detail="Tavily search timed out.")
        except httpx.HTTPError as exc:
            return SearchResultSet(
                ok=False,
                query=q,
                provider="tavily",
                detail=f"Tavily request failed: {exc.__class__.__name__}",
            )

        if resp.status_code >= 400:
            detail = "Tavily search failed."
            try:
                payload = resp.json()
                if isinstance(payload, dict):
                    err = payload.get("detail") or payload.get("error")
                    if isinstance(err, dict):
                        detail = str(err.get("error") or detail)
                    elif isinstance(err, str):
                        detail = err
            except Exception:
                detail = f"Tavily HTTP {resp.status_code}"
            return SearchResultSet(ok=False, query=q, provider="tavily", detail=detail)

        try:
            data = resp.json()
        except ValueError:
            return SearchResultSet(ok=False, query=q, provider="tavily", detail="Tavily returned invalid JSON.")

        rows: list[SearchResult] = []
        for item in data.get("results") or []:
            if not isinstance(item, dict):
                continue
            rows.append(
                SearchResult(
                    title=str(item.get("title") or "Untitled"),
                    url=str(item.get("url") or ""),
                    snippet=str(item.get("content") or item.get("snippet") or "")[:500],
                )
            )
        return SearchResultSet(ok=True, query=q, results=rows, provider="tavily", detail="")
