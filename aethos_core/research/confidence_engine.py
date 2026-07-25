# SPDX-License-Identifier: Apache-2.0
"""Research confidence + contradiction analysis."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from aethos_core.research.evidence_contract import ResearchEvidenceItem, collapse_duplicate_evidence

_AUTHORITY_DOMAINS = (
    ("docs.railway.app", 0.92),
    ("railway.app", 0.85),
    ("vercel.com", 0.9),
    ("docs.github.com", 0.92),
    ("github.com", 0.82),
    ("nextjs.org", 0.9),
    ("nodejs.org", 0.88),
)

_CONTRADICTION_PAIRS = (
    (r"\bdeprecated\b", r"\b(still active|still available|not deprecated)\b"),
    (r"\bremoved\b", r"\b(available|supported|still works)\b"),
    (r"\bbreaking change\b", r"\b(backward compatible|no breaking)\b"),
    (r"\boutage\b", r"\b(all systems operational|resolved)\b"),
)


@dataclass
class ConfidenceAnalysis:
    overall_confidence: float = 0.5
    freshness_score: float = 0.5
    source_agreement: float = 0.5
    contradictions: list[dict[str, Any]] = field(default_factory=list)
    scored_evidence: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_confidence": self.overall_confidence,
            "freshness_score": self.freshness_score,
            "source_agreement": self.source_agreement,
            "contradictions": self.contradictions,
            "scored_evidence": self.scored_evidence,
        }


def analyze_evidence(items: list[ResearchEvidenceItem], *, freshness_required: bool = False) -> ConfidenceAnalysis:
    deduped = collapse_duplicate_evidence(items)
    scored: list[dict[str, Any]] = []
    freshness_vals: list[float] = []
    confidence_vals: list[float] = []

    for item in deduped:
        fresh = _freshness_score(item.snippet, freshness_required)
        conf = _authority_score(item.url, item.provider)
        item.freshness_score = fresh
        item.confidence = conf
        freshness_vals.append(fresh)
        confidence_vals.append(conf)
        scored.append(
            {
                "citation_id": item.citation_id,
                "title": item.title,
                "url": item.url,
                "freshness_score": fresh,
                "confidence": conf,
                "provider": item.provider,
            }
        )

    contradictions = _detect_contradictions(deduped)
    agreement = max(0.2, 1.0 - (len(contradictions) * 0.2))
    overall = _mean(confidence_vals) * agreement if confidence_vals else 0.3
    if contradictions:
        overall = max(0.15, overall - 0.15)

    return ConfidenceAnalysis(
        overall_confidence=round(overall, 3),
        freshness_score=round(_mean(freshness_vals) if freshness_vals else 0.4, 3),
        source_agreement=round(agreement, 3),
        contradictions=contradictions,
        scored_evidence=scored,
    )


def _freshness_score(snippet: str, freshness_required: bool) -> float:
    text = (snippet or "").lower()
    score = 0.45
    if re.search(r"\b20(2[4-9]|3[0-9])\b", text):
        score += 0.25
    if re.search(r"\b(latest|recent|updated|today|new)\b", text):
        score += 0.2
    if freshness_required:
        score = min(1.0, score + 0.05)
    return round(min(1.0, max(0.1, score)), 3)


def _authority_score(url: str, provider: str) -> float:
    u = (url or "").lower()
    for domain, score in _AUTHORITY_DOMAINS:
        if domain in u:
            return score
    if provider == "doc_grounding":
        return 0.8
    return 0.62


def _detect_contradictions(items: list[ResearchEvidenceItem]) -> list[dict[str, Any]]:
    contradictions: list[dict[str, Any]] = []
    snippets = [(i.citation_id, i.title, (i.snippet or "").lower()) for i in items]
    for left_id, left_title, left_text in snippets:
        for right_id, right_title, right_text in snippets:
            if left_id >= right_id:
                continue
            for a_pat, b_pat in _CONTRADICTION_PAIRS:
                if re.search(a_pat, left_text) and re.search(b_pat, right_text):
                    contradictions.append(
                        {
                            "citation_a": left_id,
                            "citation_b": right_id,
                            "title_a": left_title,
                            "title_b": right_title,
                            "reason": f"Signal conflict: `{a_pat}` vs `{b_pat}`",
                        }
                    )
    return contradictions[:6]


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
