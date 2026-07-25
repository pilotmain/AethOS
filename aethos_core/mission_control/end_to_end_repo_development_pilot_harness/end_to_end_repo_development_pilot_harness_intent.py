# SPDX-License-Identifier: Apache-2.0
"""FIX 181 — chat intent for end-to-end repo development pilot harness."""

from __future__ import annotations

import re

_PILOT_HARNESS_RX = re.compile(
    r"\b("
    r"end[\s-]to[\s-]end\s+repo\s+development\s+pilot"
    r"|repo\s+development\s+pilot\s+harness"
    r"|show\s+pilot\s+harness"
    r"|pilot\s+harness\s+status"
    r"|pilot\s+stage\s+matrix"
    r")\b",
    re.I,
)

_RUN_PILOT_RX = re.compile(
    r"^\s*run\s+(?:end[\s-]to[\s-]end\s+)?pilot(?:\s+harness)?\s*$",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*pilot\s+(?P<kind>artifact|repo|issue|scope|report|forbidden|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "artifact": "pilot_artifact",
    "repo": "pilot_repo_note",
    "issue": "pilot_issue_note",
    "scope": "pilot_scope_note",
    "report": "pilot_report_note",
    "forbidden": "forbidden_pilot_note",
    "record": "end_to_end_pilot_harness_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"bypass\s+gate"
    r"|bypass\s+approval"
    r"|direct\s+provider"
    r"|autonomous\s+pilot"
    r"|hidden\s+execute"
    r"|railway\s+mutation"
    r"|merge\s+now"
    r"|deploy\s+now"
    r"|production\s+coupling"
    r")\b",
    re.I,
)


def is_end_to_end_repo_development_pilot_harness_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_PILOT_HARNESS_RX.search(raw))


def is_run_pilot_harness_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw or _FORBIDDEN_RX.search(raw):
        return False
    return bool(_RUN_PILOT_RX.match(raw))


def parse_end_to_end_repo_development_pilot_harness_record_intent(text: str) -> tuple[str, str] | None:
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
