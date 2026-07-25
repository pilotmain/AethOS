# SPDX-License-Identifier: Apache-2.0
"""Research provider abstraction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


@dataclass
class SearchResultSet:
    ok: bool
    query: str
    results: list[SearchResult] = field(default_factory=list)
    provider: str = "none"
    detail: str = ""


@dataclass
class WebsiteSummary:
    ok: bool
    url: str
    title: str = ""
    meta_description: str = ""
    headings: list[str] = field(default_factory=list)
    visible_text_preview: str = ""
    links_sample: list[str] = field(default_factory=list)
    evidence_source: str = "browser_metadata"
    artifact_ids: list[str] = field(default_factory=list)
    screenshot_artifact_id: str | None = None
    error: str | None = None
    confidence: str = "medium"


class ResearchProvider(Protocol):
    def search(self, query: str, *, max_results: int = 5) -> SearchResultSet: ...

    def summarize_url(self, url: str, *, session_id: str = "default", channel: str = "chat") -> WebsiteSummary: ...


def get_research_provider():
    from aethos_core.research.provider_factory import build_research_provider

    return build_research_provider()
