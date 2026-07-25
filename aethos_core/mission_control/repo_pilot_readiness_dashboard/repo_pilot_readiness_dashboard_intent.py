# SPDX-License-Identifier: Apache-2.0
"""FIX 182 — chat intent for repo pilot readiness dashboard."""

from __future__ import annotations

import re

_READINESS_DASHBOARD_RX = re.compile(
    r"\b("
    r"repo\s+pilot\s+readiness"
    r"|pilot\s+readiness\s+dashboard"
    r"|show\s+pilot\s+readiness"
    r"|pilot\s+preflight"
    r"|repo\s+pilot\s+preflight"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*readiness\s+(?P<kind>artifact|repo|issue|preflight|blocker|forbidden|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "artifact": "readiness_artifact",
    "repo": "repo_selection_note",
    "issue": "issue_selection_note",
    "preflight": "preflight_note",
    "blocker": "blocker_note",
    "forbidden": "forbidden_readiness_note",
    "record": "repo_pilot_readiness_dashboard_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"run\s+pilot"
    r"|bypass\s+gate"
    r"|direct\s+provider"
    r"|hidden\s+execute"
    r"|autonomous\s+pilot"
    r")\b",
    re.I,
)


def is_repo_pilot_readiness_dashboard_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_READINESS_DASHBOARD_RX.search(raw))


def parse_repo_pilot_readiness_dashboard_record_intent(text: str) -> tuple[str, str] | None:
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
