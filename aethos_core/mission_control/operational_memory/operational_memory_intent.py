# SPDX-License-Identifier: Apache-2.0
"""FIX 139 — chat intent detection for operational memory / knowledge graph."""

from __future__ import annotations

import re

_OPERATIONAL_MEMORY_RX = re.compile(
    r"\b("
    r"operational\s+memory"
    r"|knowledge\s+graph"
    r"|mission\s+lineage"
    r"|correlate\s+(?:related\s+)?executions?"
    r"|recurring\s+blockers?"
    r"|repeated\s+failures?"
    r"|historical\s+blast\s+radius"
    r"|show\s+operational\s+memory"
    r"|operational\s+memory\s+graph"
    r"|cross[- ]lane\s+memory"
    r")\b",
    re.I,
)

_FORBIDDEN_ADAPT_RX = re.compile(
    r"\b(auto[- ]?adapt|autonomous\s+learn|apply\s+memory|mutate\s+from\s+memory)\b",
    re.I,
)


def is_operational_memory_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_ADAPT_RX.search(raw):
        return False
    return bool(_OPERATIONAL_MEMORY_RX.search(raw))
