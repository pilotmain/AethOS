# SPDX-License-Identifier: Apache-2.0
"""FIX 147 — chat intent for mission readiness review board."""

from __future__ import annotations

import re

_READINESS_RX = re.compile(
    r"\b("
    r"mission\s+readiness\s+review"
    r"|readiness\s+review\s+board"
    r"|go\s*/?\s*no[- ]go"
    r"|go\s+no[- ]go"
    r"|readiness\s+board"
    r"|mission\s+readiness"
    r"|show\s+readiness\s+review"
    r"|pending\s+approvals?\s+review"
    r"|evidence\s+gaps?\s+review"
    r"|rollback\s+posture\s+review"
    r"|incident\s+exposure\s+review"
    r")\b",
    re.I,
)

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+go"
    r"|auto\s+approve\s+go"
    r"|execute\s+go\s+decision"
    r"|autonomous\s+readiness\s+decision"
    r")\b",
    re.I,
)


def is_mission_readiness_review_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_READINESS_RX.search(raw))
