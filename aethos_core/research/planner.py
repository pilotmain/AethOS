# SPDX-License-Identifier: Apache-2.0
"""Research planner — intent, mode, and provider strategy."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ResearchMode(str, Enum):
    QUICK_FACT = "quick_fact"
    OPERATIONAL = "operational"
    TECHNICAL = "technical"
    MARKET = "market"
    HIGH_FRESHNESS = "high_freshness"
    DEEP_SYNTHESIS = "deep_synthesis"


@dataclass
class ResearchPlan:
    query: str
    mode: ResearchMode
    providers: list[str] = field(default_factory=list)
    evidence_depth: str = "standard"
    freshness_required: bool = False
    browser_verification: bool = False
    max_results: int = 5
    search_queries: list[str] = field(default_factory=list)
    comparison_subjects: tuple[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "mode": self.mode.value,
            "providers": self.providers,
            "evidence_depth": self.evidence_depth,
            "freshness_required": self.freshness_required,
            "browser_verification": self.browser_verification,
            "max_results": self.max_results,
            "search_queries": self.search_queries,
            "comparison_subjects": list(self.comparison_subjects) if self.comparison_subjects else None,
        }


_OPERATIONAL_RX = re.compile(
    r"\b(deployment|rollback|railway|vercel|github actions|ci/cd|troubleshoot|incident|outage)\b",
    re.I,
)
_TECHNICAL_RX = re.compile(
    r"\b(architecture|migration|next\.?js|dependency|cve|breaking changes?|framework|api)\b",
    re.I,
)
_MARKET_RX = re.compile(r"\b(company|product|competitor|market|compare|vs\.?|ecosystem)\b", re.I)
_FRESH_RX = re.compile(r"\b(latest|recent|breaking|today|new|202[4-9])\b", re.I)
_DEEP_RX = re.compile(r"\b(compare|analysis|multi.?source|deep|comprehensive)\b", re.I)
_COMPARE_RX = re.compile(r"\bcompare\b", re.I)
_VS_RX = re.compile(r"\bvs\.?\b|\bversus\b", re.I)


def extract_research_query(text: str) -> str:
    raw = (text or "").strip()
    for pat in (
        r"^(?:research|search)\s+(?:the\s+web\s+for\s+|for\s+|latest\s+)?(.+)$",
        r"^(?:analyze|investigate)\s+(?:latest\s+)?(.+)$",
    ):
        m = re.match(pat, raw, re.I)
        if m:
            return m.group(1).strip(" ?.")
    m = re.search(r"\b(?:search|research)\s+(?:the\s+web\s+for\s+|for\s+)?(.+)$", raw, re.I)
    if m:
        return m.group(1).strip(" ?.")
    return raw


def extract_comparison_subjects(query: str) -> tuple[str, str] | None:
    """Parse 'compare A to B' / 'A vs B' style prompts."""
    raw = (query or "").strip()
    patterns = (
        r"compare\s+(.+?)\s+(?:to|with|vs\.?|versus)\s+(.+?)(?:\s+and\s+|\?|$)",
        r"(.+?)\s+vs\.?\s+(.+?)(?:\?|$)",
        r"(?:visual\s+)?comparison\s+for\s+(.+?)\s+to\s+(.+?)(?:\s+and\s+|\?|$)",
    )
    for pat in patterns:
        m = re.search(pat, raw, re.I | re.S)
        if not m:
            continue
        left = re.sub(r"\s+and\s+tell me.*$", "", m.group(1).strip(" .?"), flags=re.I).strip()
        right = re.sub(r"\s+and\s+tell me.*$", "", m.group(2).strip(" .?"), flags=re.I).strip()
        if len(left) >= 3 and len(right) >= 3:
            return left, right
    return None


def comparison_search_queries(query: str, subjects: tuple[str, str] | None = None) -> list[str]:
    pair = subjects or extract_comparison_subjects(query)
    if not pair:
        return [query, f"{query} comparison review"]
    a, b = pair
    return [
        query,
        f"{a} features overview",
        f"{b} features overview",
        f"{a} vs {b}",
        f"{a} {b} personal second brain",
    ]


def plan_research(query: str, *, max_results: int = 5) -> ResearchPlan:
    q = (query or "").strip()
    mode = ResearchMode.QUICK_FACT
    providers = ["tavily"]
    evidence_depth = "lightweight"
    freshness_required = False
    browser_verification = False

    if _COMPARE_RX.search(q) or _DEEP_RX.search(q):
        mode = ResearchMode.DEEP_SYNTHESIS
        evidence_depth = "deep"
        providers = ["tavily", "doc_grounding"]
    elif _TECHNICAL_RX.search(q):
        mode = ResearchMode.TECHNICAL
        evidence_depth = "technical"
        providers = ["tavily", "doc_grounding"]
    elif _OPERATIONAL_RX.search(q):
        mode = ResearchMode.OPERATIONAL
        evidence_depth = "operational"
        providers = ["tavily", "doc_grounding"]
        browser_verification = True
    elif _MARKET_RX.search(q):
        mode = ResearchMode.MARKET
        evidence_depth = "market"
        providers = ["tavily"]
    if _FRESH_RX.search(q):
        freshness_required = True
        if mode == ResearchMode.QUICK_FACT:
            mode = ResearchMode.HIGH_FRESHNESS

    subjects = extract_comparison_subjects(q) if (_COMPARE_RX.search(q) or _VS_RX.search(q)) else None
    search_queries = comparison_search_queries(q, subjects) if subjects or mode == ResearchMode.DEEP_SYNTHESIS else [q]

    return ResearchPlan(
        query=q,
        mode=mode,
        providers=providers,
        evidence_depth=evidence_depth,
        freshness_required=freshness_required,
        browser_verification=browser_verification,
        max_results=max_results,
        search_queries=search_queries,
        comparison_subjects=subjects,
    )
