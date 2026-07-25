# SPDX-License-Identifier: Apache-2.0
"""FIX 158 — chat intent for institutional existential risk."""

from __future__ import annotations

import re

_EXISTENTIAL_RISK_RX = re.compile(
    r"\b("
    r"institutional\s+existential\s+risk"
    r"|existential\s+continuity"
    r"|continuity\s+preservation"
    r"|constitutional\s+continuity\s+risk"
    r"|institutional\s+dependency\s+concentration"
    r"|governance\s+collapse\s+scenario"
    r"|mission\s+identity\s+erosion"
    r"|sovereignty\s+degradation"
    r"|institutional\s+fragility"
    r"|civilization[\-\s]scale\s+dependency"
    r"|constitutional\s+extinction"
    r"|institutional\s+preservation\s+scoring"
    r"|show\s+existential\s+risk"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*existential\s+(?P<kind>continuity|dependency|collapse|erosion|sovereignty|preservation)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "continuity": "continuity_risk_observation",
    "dependency": "dependency_concentration_note",
    "collapse": "collapse_scenario",
    "erosion": "identity_erosion_signal",
    "sovereignty": "sovereignty_degradation_note",
    "preservation": "preservation_recommendation",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+self[\-\s]?preservation"
    r"|autonomous\s+continuity\s+enforcement"
    r"|constitutional\s+override\s+authority"
    r"|institutional\s+self[\-\s]?defense\s+authority"
    r"|auto\s+preserve\s+institution"
    r"|enforce\s+continuity\s+autonomously"
    r")\b",
    re.I,
)


def is_institutional_existential_risk_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_EXISTENTIAL_RISK_RX.search(raw))


def parse_existential_risk_record_intent(text: str) -> tuple[str, str] | None:
    raw = (text or "").strip()
    if not raw or _FORBIDDEN_RX.search(raw):
        return None
    match = _RECORD_RX.match(raw)
    if not match:
        return None
    kind = _KIND_MAP.get(match.group("kind").lower())
    if not kind:
        return None
    body = (match.group("body") or "").strip()
    if not body:
        return None
    return kind, body
