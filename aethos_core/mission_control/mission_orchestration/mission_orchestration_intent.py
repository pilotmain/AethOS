# SPDX-License-Identifier: Apache-2.0
"""FIX 146 — chat intent for coordinated mission orchestration."""

from __future__ import annotations

import re

_ORCHESTRATION_RX = re.compile(
    r"\b("
    r"mission\s+orchestration"
    r"|coordinated\s+mission\s+orchestration"
    r"|orchestration\s+coordination"
    r"|mission\s+dependency\s+graph"
    r"|lane\s+synchronization"
    r"|orchestration\s+readiness"
    r"|operator\s+sequencing"
    r"|approval\s+batching"
    r"|cross[- ]lane\s+mission\s+health"
    r"|show\s+mission\s+orchestration"
    r"|governed\s+stage\s+orchestration"
    r"|blocked[- ]by\s+relationships?"
    r")\b",
    re.I,
)

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+sequenc"
    r"|auto\s+batch\s+approv"
    r"|execute\s+orchestration"
    r"|autonomous\s+promot"
    r"|autonomous\s+deploy"
    r"|auto\s+orchestrat"
    r")\b",
    re.I,
)


def is_mission_orchestration_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_ORCHESTRATION_RX.search(raw))
