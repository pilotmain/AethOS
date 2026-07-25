# SPDX-License-Identifier: Apache-2.0
"""FIX 250 — chat intent for governed application generation."""

from __future__ import annotations

import re
from typing import Any

_VIEW_RX = re.compile(
    r"\b("
    r"show\s+(?:governed\s+)?application\s+generation"
    r"|generation\s+readiness\s+report"
    r"|governed\s+application\s+generation"
    r"|product\s+creation\s+pipeline"
    r")\b",
    re.I,
)

_HANDOFF_RX = re.compile(
    r"\b(prepare\s+delivery\s+pipeline\s+handoff|feed\s+existing\s+delivery\s+pipeline)\b",
    re.I,
)

_PRD_RX = re.compile(r"^\s*prd\s+intake\s*:\s*(?P<body>.+)$", re.I | re.S)
_VISION_RX = re.compile(r"^\s*product\s+vision\s*:\s*(?P<body>.+)$", re.I | re.S)
_REQ_RX = re.compile(r"^\s*requirements\s*:\s*(?P<body>.+)$", re.I | re.S)
_CONST_RX = re.compile(r"^\s*constraints\s*:\s*(?P<body>.+)$", re.I | re.S)
_ARCH_RX = re.compile(r"^\s*architecture\s+package\s*:\s*(?P<body>.+)$", re.I | re.S)
_BLUE_RX = re.compile(r"^\s*repository\s+blueprint\s*:\s*(?P<body>.+)$", re.I | re.S)
_BACK_RX = re.compile(r"^\s*delivery\s+backlog\s*:\s*(?P<body>.+)$", re.I | re.S)

_DECISION_RX = re.compile(
    r"^\s*generation\s+decision\s+(?P<decision>approve|hold|reject)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_DECISION_KIND_MAP = {
    "approve": "generation_decision_approve",
    "hold": "generation_decision_hold",
    "reject": "generation_decision_reject",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"create\s+repository\s+now"
    r"|generate\s+code\s+now"
    r"|autonomous\s+deploy"
    r"|github\s+create\s+repo"
    r")\b",
    re.I,
)

_PRODUCT_RX = re.compile(r"\bproduct\s*=\s*([^\n]+)", re.I)


def _parse_prd_metadata(text: str) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    match = _PRODUCT_RX.search(text or "")
    if match:
        meta["product_name"] = match.group(1).strip()[:80]
    return meta


def is_governed_application_generation_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(
        _VIEW_RX.search(raw)
        or _HANDOFF_RX.search(raw)
        or _PRD_RX.match(raw)
        or _VISION_RX.match(raw)
        or _REQ_RX.match(raw)
        or _CONST_RX.match(raw)
        or _ARCH_RX.match(raw)
        or _BLUE_RX.match(raw)
        or _BACK_RX.match(raw)
        or _DECISION_RX.match(raw)
    )


def is_governed_application_generation_handoff_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw or _FORBIDDEN_RX.search(raw):
        return False
    return bool(_HANDOFF_RX.search(raw))


def parse_governed_application_generation_record_intent(
    text: str,
) -> tuple[str, str, dict[str, Any]] | None:
    raw = (text or "").strip()

    decision_match = _DECISION_RX.match(raw)
    if decision_match:
        kind = _DECISION_KIND_MAP.get(decision_match.group("decision").lower())
        body = (decision_match.group("body") or "").strip()
        if kind and body:
            return kind, body, {}

    parsers: tuple[tuple[Any, str, Any], ...] = (
        (_PRD_RX, "prd_intake_note", _parse_prd_metadata),
        (_VISION_RX, "product_vision_note", lambda _: {}),
        (_REQ_RX, "requirements_note", lambda _: {}),
        (_CONST_RX, "constraints_note", lambda _: {}),
        (_ARCH_RX, "architecture_package_note", lambda _: {}),
        (_BLUE_RX, "repository_blueprint_note", lambda _: {}),
        (_BACK_RX, "delivery_backlog_note", lambda _: {}),
    )
    for pattern, kind, meta_fn in parsers:
        match = pattern.match(raw)
        if match:
            body = (match.group("body") or "").strip()
            if body:
                return kind, body, meta_fn(body)
    return None
