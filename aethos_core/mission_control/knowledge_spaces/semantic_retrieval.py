# SPDX-License-Identifier: Apache-2.0
"""FIX 141 — lightweight semantic scoring for operational knowledge documents."""

from __future__ import annotations

import re
from typing import Any

_TOKEN_RX = re.compile(r"[a-z0-9_./-]{2,}", re.I)

_STOPWORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "this",
        "that",
        "with",
        "from",
        "have",
        "has",
        "been",
        "what",
        "when",
        "where",
        "show",
        "search",
        "find",
        "mission",
        "operational",
        "memory",
        "before",
    }
)


def tokenize(text: str) -> set[str]:
    tokens = {t.lower() for t in _TOKEN_RX.findall(text or "") if t.lower() not in _STOPWORDS}
    return tokens


def semantic_similarity(*, query: str, document_text: str, category: str = "") -> float:
    """Token-overlap similarity with phrase and category boosts (0.0–1.0)."""
    q = (query or "").strip().lower()
    doc = (document_text or "").strip().lower()
    if not q or not doc:
        return 0.0

    if q in doc:
        return min(1.0, 0.85 + len(q) / max(len(doc), 1) * 0.1)

    q_tokens = tokenize(q)
    d_tokens = tokenize(doc)
    if not q_tokens or not d_tokens:
        return 0.0

    overlap = q_tokens & d_tokens
    if not overlap:
        return 0.0

    jaccard = len(overlap) / len(q_tokens | d_tokens)
    recall = len(overlap) / len(q_tokens)
    score = 0.45 * jaccard + 0.55 * recall

    cat = (category or "").lower()
    if cat and cat in q:
        score = min(1.0, score + 0.08)

    return round(min(1.0, score), 4)


def rank_documents(
    *,
    query: str,
    documents: list[dict[str, Any]],
    limit: int = 20,
) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for doc in documents:
        text = str(doc.get("text") or "")
        cat = str(doc.get("category") or "")
        score = semantic_similarity(query=query, document_text=text, category=cat)
        if score <= 0.05:
            continue
        row = dict(doc)
        row["relevance_score"] = score
        ranked.append(row)
    ranked.sort(
        key=lambda r: (float(r.get("relevance_score") or 0), str(r.get("recorded_at") or "")),
        reverse=True,
    )
    return ranked[:limit]
