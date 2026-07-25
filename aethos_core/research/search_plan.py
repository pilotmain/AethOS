# SPDX-License-Identifier: Apache-2.0
"""Governed web research — provenance-first (dry-run foundation)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResearchSource:
    url: str
    title: str = ""
    reliability: str = "unknown"
    snippet: str = ""


@dataclass
class ResearchPlan:
    query: str
    sources: list[ResearchSource] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    dry_run: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "dry_run": self.dry_run,
            "sources": [s.__dict__ for s in self.sources],
            "citations": self.citations,
            "provenance_required": True,
        }


def build_research_plan_dry_run(query: str) -> ResearchPlan:
    return ResearchPlan(
        query=query,
        dry_run=True,
        citations=[f"Research plan for: {query} (no live search executed — design foundation)"],
    )
