# SPDX-License-Identifier: Apache-2.0
"""FIX 168 — chat intent for bounded delivery work packages."""

from __future__ import annotations

import re

_WORK_PACKAGES_RX = re.compile(
    r"\b("
    r"bounded\s+delivery\s+work\s+packages?"
    r"|delivery\s+work\s+packages?"
    r"|work\s+packages?"
    r"|role[\-\s]scoped\s+packages?"
    r"|agent\s+package\s+assignments?"
    r"|package\s+inputs?"
    r"|package\s+gates?"
    r"|package\s+forbidden"
    r"|delivery\s+integrity"
    r"|show\s+work\s+packages?"
    r"|show\s+delivery\s+packages?"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*work\s+package\s+(?P<kind>artifact|planner|risk|verification|delivery|diff\s*audit|gate|forbidden|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "artifact": "work_package_artifact",
    "planner": "planner_package_note",
    "risk": "risk_package_note",
    "verification": "verification_package_note",
    "delivery": "delivery_package_note",
    "diff audit": "diff_audit_package_note",
    "diffaudit": "diff_audit_package_note",
    "gate": "package_gate_note",
    "forbidden": "package_forbidden_note",
    "record": "delivery_work_packages_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+execution"
    r"|write\s+code"
    r"|open\s+pr"
    r"|merge\s+deploy"
    r"|mutate\s+railway"
    r"|execute\s+work\s+package"
    r"|run\s+delivery\s+autonomously"
    r")\b",
    re.I,
)


def is_bounded_delivery_work_packages_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_WORK_PACKAGES_RX.search(raw))


def parse_work_packages_record_intent(text: str) -> tuple[str, str] | None:
    raw = (text or "").strip()
    if not raw or _FORBIDDEN_RX.search(raw):
        return None
    match = _RECORD_RX.match(raw)
    if not match:
        return None
    kind_key = re.sub(r"\s+", " ", match.group("kind").lower()).strip()
    kind = _KIND_MAP.get(kind_key)
    if not kind:
        return None
    body = (match.group("body") or "").strip()
    if not body:
        return None
    return kind, body
