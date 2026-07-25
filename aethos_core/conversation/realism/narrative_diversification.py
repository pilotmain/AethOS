# SPDX-License-Identifier: Apache-2.0
"""Narrative diversification — reduce formulaic operational prose repetition."""

from __future__ import annotations

import hashlib
from typing import Any

_MONITORING_CLOSINGS = (
    "I'm keeping extended observation active until long-running behavior is confirmed stable.",
    "Sustained observation continues — I'm not treating this as fully settled yet.",
    "I'm still watching for regression signals before calling this fully durable.",
    "Longer-horizon verification remains in progress alongside current healthy signals.",
)

_STABILITY_OPENINGS = (
    "The current picture looks bounded and improving.",
    "Operational signals remain within acceptable recovery bounds.",
    "Recovery indicators are holding without new acceleration patterns.",
    "The active thread still reads as stable under current checks.",
)

_UNCERTAINTY_PREFIXES = (
    "I believe you're referring to the earlier {subject} thread, though operational context confidence is currently limited.",
    "My best read is that you're asking about {subject}, but continuity confidence is moderate — I'll stay honest about uncertainty.",
    "I'm reconstructing this around {subject}, though the operational thread match isn't fully certain.",
)


def _pick(pool: tuple[str, ...], *, session_id: str, salt: str) -> str:
    digest = hashlib.sha256(f"{session_id}:{salt}".encode()).hexdigest()
    return pool[int(digest[:8], 16) % len(pool)]


def diversify_monitoring_close(*, session_id: str = "default") -> str:
    return _pick(_MONITORING_CLOSINGS, session_id=session_id, salt="monitoring")


def diversify_stability_opening(*, session_id: str = "default") -> str:
    return _pick(_STABILITY_OPENINGS, session_id=session_id, salt="stability")


def uncertain_continuity_prefix(*, subject: str, session_id: str = "default") -> str:
    template = _pick(_UNCERTAINTY_PREFIXES, session_id=session_id, salt="uncertain")
    return template.format(subject=subject)


def assess_narrative_entropy(*, recent_phrases: list[str] | None = None) -> dict[str, Any]:
    phrases = recent_phrases or []
    repeated = len(phrases) != len(set(p.lower() for p in phrases if p))
    return {
        "entropy_active": True,
        "rotation_enabled": True,
        "repetition_detected": repeated,
        "summary": "Narrative diversification active — operational prose rotation enabled.",
    }
