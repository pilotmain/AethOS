# SPDX-License-Identifier: Apache-2.0
"""FIX 144 — chat intent for governance simulation sandbox."""

from __future__ import annotations

import re

_SIMULATION_RX = re.compile(
    r"\b("
    r"governance\s+simulation"
    r"|simulate\s+(?:alternate\s+)?approval\s+chain"
    r"|simulate\s+(?:reduced|increased)\s+quorum"
    r"|simulate\s+rollout\s+policy"
    r"|simulate\s+(?:stricter\s+)?verification"
    r"|compare\s+governance\s+configurations?"
    r"|governance\s+sandbox"
    r"|governance\s+experiment"
    r"|what\s+if\s+governance"
    r")\b",
    re.I,
)

_FORBIDDEN_RX = re.compile(
    r"\b(apply\s+simulation|auto[- ]?tune|mutate\s+policy|enable\s+simulated\s+policy|live\s+policy\s+change)\b",
    re.I,
)


def is_governance_simulation_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_SIMULATION_RX.search(raw))
