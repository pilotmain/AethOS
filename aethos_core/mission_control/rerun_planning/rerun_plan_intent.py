# SPDX-License-Identifier: Apache-2.0
"""FIX 138 — chat intent detection for governed rerun planning."""

from __future__ import annotations

import re

_RERUN_PLAN_RX = re.compile(
    r"\b("
    r"governed\s+rerun\s+plan(?:ning)?"
    r"|rerun\s+eligibility"
    r"|rerun\s+plan\b"
    r"|what\s+would\s+happen\s+if\s+we\s+rerun"
    r"|analyze\s+rerun\b"
    r"|show\s+rerun\s+plan"
    r")\b",
    re.I,
)

# Explicit execution attempts must not be treated as planning.
_FORBIDDEN_EXECUTE_RX = re.compile(
    r"\b(execute\s+rerun|rerun\s+now|perform\s+rerun|trigger\s+rerun)\b",
    re.I,
)


def is_governed_rerun_plan_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_EXECUTE_RX.search(raw):
        return False
    return bool(_RERUN_PLAN_RX.search(raw))
