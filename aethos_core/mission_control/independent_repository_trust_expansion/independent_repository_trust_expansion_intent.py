# SPDX-License-Identifier: Apache-2.0
"""FIX 187 — chat intent for independent repository trust expansion."""

from __future__ import annotations

import re

_TRUST_EXPANSION_RX = re.compile(
    r"\b("
    r"repository\s+trust\s+(?:expansion|registry|matrix)"
    r"|independent\s+repo\s+trust"
    r"|show\s+repository\s+trust"
    r"|repo\s+trust\s+expansion"
    r"|phase\s+2\s+dogfood\s+expansion"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*repo\s+(?P<kind>expansion|evidence|trust|skip)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "expansion": "repo_expansion_approval",
    "evidence": "repo_pilot_evidence_note",
    "trust": "trust_registry_note",
    "skip": "sequence_skip_approval",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"run\s+pilot"
    r"|inherit\s+trust"
    r"|transfer\s+trust"
    r"|auto\s+expand"
    r"|bypass\s+gate"
    r")\b",
    re.I,
)


def is_independent_repository_trust_expansion_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_TRUST_EXPANSION_RX.search(raw))


def parse_independent_repository_trust_expansion_record_intent(text: str) -> tuple[str, str] | None:
    raw = (text or "").strip()
    if not raw:
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
