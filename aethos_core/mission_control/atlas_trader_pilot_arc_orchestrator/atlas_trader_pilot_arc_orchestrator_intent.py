# SPDX-License-Identifier: Apache-2.0
"""FIX 193 — chat intent for Atlas Trader pilot arc orchestrator."""

from __future__ import annotations

import re

_PILOT_ARC_RX = re.compile(
    r"\b("
    r"atlas\s+(?:trader\s+)?pilot\s+arc"
    r"|show\s+atlas\s+pilot"
    r"|atlas\s+pilot\s+status"
    r"|atlas\s+pilot\s+dashboard"
    r")\b",
    re.I,
)

_RUN_PILOT_RX = re.compile(
    r"\brun\s+atlas\s+pilot\s+(?P<num>[123])\b",
    re.I,
)

_ATLAS_RECORD_RX = re.compile(
    r"^\s*atlas\s+pilot\s+arc\s+(?P<kind>issue|note)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_ATLAS_OBS_RX = re.compile(
    r"^\s*atlas\s+pilot\s+(?P<kind>observation|intervention)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "issue": "repo_issue_binding",
    "note": "pilot_arc_note",
}

_OBS_KIND_MAP = {
    "observation": "atlas_pilot_observation",
    "intervention": "atlas_pilot_intervention",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"auto\s+trust"
    r"|inherit\s+trust"
    r"|bypass\s+gate"
    r"|hidden\s+run"
    r")\b",
    re.I,
)


def is_atlas_trader_pilot_arc_orchestrator_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_PILOT_ARC_RX.search(raw))


def parse_run_atlas_pilot_intent(text: str) -> int | None:
    raw = (text or "").strip()
    match = _RUN_PILOT_RX.search(raw)
    if not match:
        return None
    return int(match.group("num"))


def parse_atlas_trader_pilot_arc_orchestrator_record_intent(text: str) -> tuple[str, str] | None:
    raw = (text or "").strip()
    if not raw:
        return None

    obs_match = _ATLAS_OBS_RX.match(raw)
    if obs_match:
        kind = _OBS_KIND_MAP.get(obs_match.group("kind").lower())
        if not kind:
            return None
        body = (obs_match.group("body") or "").strip()
        if not body:
            return None
        return kind, body

    match = _ATLAS_RECORD_RX.match(raw)
    if not match:
        return None
    kind = _KIND_MAP.get(match.group("kind").lower())
    if not kind:
        return None
    body = (match.group("body") or "").strip()
    if not body:
        return None
    return kind, body
