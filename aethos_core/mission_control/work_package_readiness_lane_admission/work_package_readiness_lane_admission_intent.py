# SPDX-License-Identifier: Apache-2.0
"""FIX 169 — chat intent for work package readiness + lane admission."""

from __future__ import annotations

import re

_LANE_ADMISSION_RX = re.compile(
    r"\b("
    r"work\s+package\s+readiness"
    r"|lane\s+admission"
    r"|package\s+readiness"
    r"|admission\s+blockers?"
    r"|lane\s+admission\s+package"
    r"|admission\s+artifact"
    r"|eligible\s+for\s+lane"
    r"|show\s+lane\s+admission"
    r"|show\s+package\s+readiness"
    r"|readiness\s+check"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*admission\s+(?P<kind>artifact|readiness|blocker|lane|prerequisite|forbidden|record)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "artifact": "lane_admission_artifact",
    "readiness": "readiness_check_note",
    "blocker": "admission_blocker_note",
    "lane": "lane_mapping_note",
    "prerequisite": "prerequisite_note",
    "forbidden": "admission_forbidden_note",
    "record": "lane_admission_record",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+lane\s+entry"
    r"|enter\s+lane\s+autonomously"
    r"|write\s+code"
    r"|open\s+pr"
    r"|merge\s+deploy"
    r"|mutate\s+railway"
    r"|execute\s+admission"
    r")\b",
    re.I,
)


def is_work_package_readiness_lane_admission_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_LANE_ADMISSION_RX.search(raw))


def parse_lane_admission_record_intent(text: str) -> tuple[str, str] | None:
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
