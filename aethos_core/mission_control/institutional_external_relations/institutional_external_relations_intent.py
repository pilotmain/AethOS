# SPDX-License-Identifier: Apache-2.0
"""FIX 157 — chat intent for institutional external relations."""

from __future__ import annotations

import re

_EXTERNAL_RELATIONS_RX = re.compile(
    r"\b("
    r"institutional\s+external\s+relations"
    r"|constitutional\s+boundary"
    r"|external\s+provider\s+relationship"
    r"|external\s+trust\s+classification"
    r"|ecosystem\s+dependency"
    r"|external\s+governance\s+interaction"
    r"|provider\s+sovereignty\s+boundary"
    r"|constitutional\s+interoperability"
    r"|institutional\s+dependency\s+risk"
    r"|external\s+influence\s+drift"
    r"|cross[\-\s]system\s+trust"
    r"|show\s+external\s+relations"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*external\s+(?P<kind>provider|boundary|trust|dependency|policy|influence)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "provider": "provider_relationship",
    "boundary": "boundary_definition",
    "trust": "trust_classification",
    "dependency": "dependency_lineage",
    "policy": "interaction_policy",
    "influence": "influence_observation",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+external\s+negotiation"
    r"|autonomous\s+provider\s+alignment"
    r"|self[\-\s]?directed\s+institutional\s+diplomacy"
    r"|sovereignty\s+delegation"
    r"|auto\s+negotiate\s+external"
    r"|delegate\s+sovereignty"
    r")\b",
    re.I,
)


def is_institutional_external_relations_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_EXTERNAL_RELATIONS_RX.search(raw))


def parse_external_relations_record_intent(text: str) -> tuple[str, str] | None:
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
