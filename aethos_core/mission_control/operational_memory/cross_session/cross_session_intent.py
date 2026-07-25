# SPDX-License-Identifier: Apache-2.0
"""FIX 140 — chat intent for cross-session organizational memory."""

from __future__ import annotations

import re

_CROSS_SESSION_RX = re.compile(
    r"\b("
    r"cross[- ]?session\s+operational\s+memory"
    r"|organizational\s+memory"
    r"|organizational\s+memory\s+layer"
    r"|mission\s+ancestry\s+across\s+sessions?"
    r"|correlate\s+missions?\s+across\s+sessions?"
    r"|historical\s+blockers?\s+across\s+sessions?"
    r"|operator\s+history"
    r"|cross[- ]?session\s+memory"
    r"|durable\s+operational\s+memory"
    r"|evidence\s+stitching"
    r")\b",
    re.I,
)

_FORBIDDEN_RX = re.compile(
    r"\b(auto[- ]?adapt|autonomous\s+optimi|mutate\s+from\s+memory|apply\s+organizational)\b",
    re.I,
)


def is_cross_session_memory_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_CROSS_SESSION_RX.search(raw))
