# SPDX-License-Identifier: Apache-2.0
"""Thread isolation — score investigation thread separation."""

from __future__ import annotations

from typing import Any


def score_thread_isolation(
    *,
    investigations: list[str],
    focus_topics: list[str],
    primary_subject: str | None = None,
) -> dict[str, Any]:
    """Detect when multiple operational threads may be conflated."""
    invs = [i for i in investigations if i]
    topics = [t for t in focus_topics if t]
    unique = list(dict.fromkeys(invs + topics))
    overlap = len(invs) + len(topics) - len(unique)

    isolation_score = 1.0
    if len(invs) >= 2:
        isolation_score -= 0.25 * (len(invs) - 1)
    if len(unique) >= 4:
        isolation_score -= 0.15
    if overlap > 0:
        isolation_score -= 0.1 * overlap

    isolation_score = max(0.2, min(1.0, isolation_score))
    conflated = isolation_score < 0.55 and len(invs) >= 2

    return {
        "isolation_score": round(isolation_score, 2),
        "investigation_count": len(invs),
        "unique_thread_count": len(unique),
        "conflated": conflated,
        "summary": "Thread isolation healthy." if not conflated else "Multiple investigations may be conflated — isolation recommended.",
    }
