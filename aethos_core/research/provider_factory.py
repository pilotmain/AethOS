# SPDX-License-Identifier: Apache-2.0
"""Research provider factory — single settings authority."""

from __future__ import annotations

from typing import Any

from aethos_core.config import Settings, get_settings
from aethos_core.research.research_config import is_research_search_configured
from aethos_core.research.research_provider import ResearchProvider, SearchResultSet, WebsiteSummary


class DisabledSearchProvider:
    def search(self, query: str, *, max_results: int = 5) -> SearchResultSet:
        return SearchResultSet(
            ok=False,
            query=query,
            provider="disabled",
            detail="WEB_RESEARCH_ENABLED is false.",
        )


class NotConfiguredSearchProvider:
    def __init__(self, *, reason: str = "Web search provider is not configured.") -> None:
        self._reason = reason

    def search(self, query: str, *, max_results: int = 5) -> SearchResultSet:
        return SearchResultSet(ok=False, query=query, provider="none", detail=self._reason)


class CompositeResearchProvider:
    """Browser-backed URL inspection + configured search provider."""

    def __init__(self, search_provider: Any, summarize_provider: Any) -> None:
        self._search = search_provider
        self._summarize = summarize_provider

    def search(self, query: str, *, max_results: int = 5) -> SearchResultSet:
        return self._search.search(query, max_results=max_results)

    def summarize_url(self, url: str, *, session_id: str = "default", channel: str = "chat") -> WebsiteSummary:
        return self._summarize.summarize_url(url, session_id=session_id, channel=channel)


def build_search_provider(settings: Settings | None = None) -> Any:
    s = settings or get_settings()
    if not s.web_research_enabled:
        return DisabledSearchProvider()
    provider = (s.web_search_provider or "none").strip().lower()
    api_key = (s.web_search_api_key or "").strip()
    base_url = (getattr(s, "web_search_base_url", None) or "").strip()
    if provider == "tavily" and api_key:
        from aethos_core.research.providers.tavily_provider import TavilyResearchProvider

        return TavilyResearchProvider(api_key)
    if provider == "tavily" and not api_key:
        return NotConfiguredSearchProvider(reason="WEB_SEARCH_API_KEY is missing for Tavily.")
    if provider == "searxng" and base_url:
        from aethos_core.research.providers.searxng_provider import SearxngResearchProvider

        return SearxngResearchProvider(base_url)
    if provider == "searxng" and not base_url:
        return NotConfiguredSearchProvider(reason="WEB_SEARCH_BASE_URL is missing for SearXNG.")
    if provider in ("none", "", "disabled"):
        return NotConfiguredSearchProvider(reason="WEB_SEARCH_PROVIDER is missing or none.")
    return NotConfiguredSearchProvider(reason=f"Unsupported WEB_SEARCH_PROVIDER: {provider}")


def build_research_provider(settings: Settings | None = None) -> ResearchProvider:
    from aethos_core.research.website_summary import BrowserBackedResearchProvider

    s = settings or get_settings()
    return CompositeResearchProvider(
        search_provider=build_search_provider(s),
        summarize_provider=BrowserBackedResearchProvider(),
    )


def research_provider_label(settings: Settings | None = None) -> str:
    s = settings or get_settings()
    if not is_research_search_configured(s):
        return "none"
    return (s.web_search_provider or "none").strip().lower()
