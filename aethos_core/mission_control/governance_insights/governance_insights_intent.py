# SPDX-License-Identifier: Apache-2.0
"""FIX 143 — chat intent for meta-governance insights."""

from __future__ import annotations

import re

_INSIGHTS_RX = re.compile(
    r"\b("
    r"governance\s+insights?"
    r"|meta[- ]?governance"
    r"|adaptive\s+governance\s+insights?"
    r"|governance\s+health"
    r"|approval\s+bottlenecks?"
    r"|governance\s+friction"
    r"|operator\s+workload\s+heatmap"
    r"|mission\s+completion\s+latency"
    r"|governance\s+telemetry"
    r"|show\s+governance\s+insights?"
    r")\b",
    re.I,
)

_FORBIDDEN_RX = re.compile(
    r"\b(auto[- ]?tune\s+policy|modify\s+governance|self[- ]?modif(?:y|ying)\s+governance|autonomous\s+optimi)\b",
    re.I,
)


def is_governance_insights_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_INSIGHTS_RX.search(raw))
