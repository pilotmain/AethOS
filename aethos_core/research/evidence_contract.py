# SPDX-License-Identifier: Apache-2.0
"""Normalized research evidence contract."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import time
from typing import Any
from uuid import uuid4


def new_citation_id() -> str:
    return f"re-{uuid4().hex[:8]}"


@dataclass
class ResearchEvidenceItem:
    source_type: str
    provider: str
    title: str
    url: str
    snippet: str
    freshness_score: float = 0.5
    confidence: float = 0.5
    retrieved_at: float = field(default_factory=time)
    citation_id: str = field(default_factory=new_citation_id)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_search_hit(
    *,
    provider: str,
    title: str,
    url: str,
    snippet: str,
    source_type: str = "web",
    metadata: dict[str, Any] | None = None,
) -> ResearchEvidenceItem:
    return ResearchEvidenceItem(
        source_type=source_type,
        provider=provider,
        title=(title or "Untitled").strip(),
        url=(url or "").strip(),
        snippet=(snippet or "").strip()[:800],
        metadata=metadata or {},
    )


def collapse_duplicate_evidence(items: list[ResearchEvidenceItem]) -> list[ResearchEvidenceItem]:
    seen: set[str] = set()
    out: list[ResearchEvidenceItem] = []
    for item in items:
        key = (item.url or item.title).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out
