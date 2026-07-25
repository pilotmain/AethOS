# SPDX-License-Identifier: Apache-2.0
"""FIX 145 — chat intent for mission strategy layer."""

from __future__ import annotations

import re

_STRATEGY_RX = re.compile(
    r"\b("
    r"mission\s+strategy"
    r"|strategic\s+(?:operational\s+)?reasoning"
    r"|operational\s+drift"
    r"|long[- ]running\s+mission\s+themes?"
    r"|strategic\s+bottlenecks?"
    r"|governance\s+maturity\s+priorities?"
    r"|high[- ]friction\s+mission"
    r"|organizational\s+risk\s+concentration"
    r"|show\s+mission\s+strategy"
    r"|strategic\s+cognition"
    r")\b",
    re.I,
)

_FORBIDDEN_RX = re.compile(
    r"\b(autonomous\s+plan|auto\s+reprioriti|self[- ]?direct|execute\s+strategy|mutate\s+policy)\b",
    re.I,
)


def is_mission_strategy_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_STRATEGY_RX.search(raw))
