# SPDX-License-Identifier: Apache-2.0
"""Recommendation curator — human-quality recommendations."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.synthesis_pkg.intent_contracts import IntentContract
from aethos_core.recommendation_intelligence.audience_awareness import apply_audience_context
from aethos_core.recommendation_intelligence.geographic_normalization import normalize_geography
from aethos_core.recommendation_intelligence.recommendation_explanations import build_explanation
from aethos_core.recommendation_intelligence.source_weighting import weight_sources


def evidence_to_recommendations(evidence: list[Any], *, contract: IntentContract) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for e in evidence:
        title = getattr(e, "title", None) or (e.get("title") if isinstance(e, dict) else "")
        snippet = getattr(e, "snippet", None) or (e.get("snippet") if isinstance(e, dict) else "")
        conf = float(getattr(e, "confidence", 0.5) if not isinstance(e, dict) else e.get("confidence", 0.5))
        items.append({
            "name": _extract_name(str(title), str(snippet)),
            "location": normalize_geography(str(title) + " " + str(snippet), filter_region=contract.geographic_filter),
            "description": (str(snippet) or str(title))[:240].strip(),
            "score": weight_sources(confidence=conf, provider=str(getattr(e, "provider", "") or "")),
            "source_title": str(title),
        })
    if contract.audience:
        items = apply_audience_context(items, audience=contract.audience)
    for item in items:
        item["explanation"] = build_explanation(item)
    return items


def _extract_name(title: str, snippet: str) -> str:
    for text in (title, snippet):
        if " — " in text:
            return text.split(" — ")[0].strip()
        if " - " in text:
            return text.split(" - ")[0].strip()
    return (title or snippet or "Recommendation")[:80].strip()
